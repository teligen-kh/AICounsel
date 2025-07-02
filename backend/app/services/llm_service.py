from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_mongodb import MongoDBChatMessageHistory
from ..config import settings
from .mongodb_search_service import MongoDBSearchService
from .conversation_algorithm import ConversationAlgorithm
from .formatting_service import FormattingService
from .model_manager import get_model_manager, ModelType
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from enum import Enum
import asyncio

class IntentType(Enum):
    """사용자 의도 타입"""
    CASUAL = "casual"  # 일상 대화
    PROFESSIONAL = "professional"  # 전문 상담
    GREETING = "greeting"  # 인사
    QUESTION = "question"  # 질문
    COMPLAINT = "complaint"  # 불만/문제
    REQUEST = "request"  # 요청
    THANKS = "thanks"  # 감사
    UNKNOWN = "unknown"  # 알 수 없음

class LLMService:
    def __init__(self, db: AsyncIOMotorDatabase = None, use_db_priority: bool = True, model_type: str = ModelType.POLYGLOT_KO_5_8B.value):
        """
        LLM 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결
            use_db_priority: DB 우선 검색 모드 사용 여부
            model_type: 사용할 모델 타입
        """
        self.db = db
        self.use_db_priority = use_db_priority
        self.model_type = model_type
        
        # 모델 매니저 가져오기
        self.model_manager = get_model_manager()
        
        # MongoDB 검색 서비스 초기화
        if db is not None and use_db_priority:
            self.search_service = MongoDBSearchService(db)
        else:
            self.search_service = None
        
        # 고객 응대 알고리즘 초기화
        self.conversation_algorithm = ConversationAlgorithm()
        
        # 응답 시간 통계 초기화
        self.response_stats = {
            'total_requests': 0,
            'casual_conversations': 0,
            'professional_conversations': 0,
            'db_responses': 0,
            'llama_responses': 0,
            'errors': 0,
            'total_processing_time': 0,
            'db_processing_time': 0,
            'llama_processing_time': 0,
            'error_processing_time': 0,
            'min_processing_time': float('inf'),
            'max_processing_time': 0,
            'processing_times': []  # 모든 처리 시간 기록
        }
        
        # 모델 로딩
        self._load_model_sync(model_type)

    def _load_model_sync(self, model_type: str):
        """모델을 동기적으로 로딩합니다."""
        try:
            logging.info(f"Loading model: {model_type}")
            success = self.model_manager.load_model(model_type)
            if success:
                logging.info(f"Model {model_type} loaded successfully")
            else:
                logging.error(f"Failed to load model {model_type}")
        except Exception as e:
            logging.error(f"Failed to load model {model_type}: {str(e)}")
    
    def switch_model(self, model_type: str) -> bool:
        """다른 모델로 전환합니다."""
        try:
            success = self.model_manager.switch_model(model_type)
            if success:
                self.model_type = model_type
                logging.info(f"Switched to model: {model_type}")
            return success
        except Exception as e:
            logging.error(f"Failed to switch model: {str(e)}")
            return False
    
    def get_current_model(self):
        """현재 모델을 반환합니다."""
        return self.model_manager.get_current_model()
    
    def get_current_model_config(self):
        """현재 모델 설정을 반환합니다."""
        return self.model_manager.get_current_model_config()

    def _load_model_async(self, model_path: str):
        """모델을 비동기로 로딩합니다."""
        import threading
        
        def load_model():
            try:
                logging.info("Loading LLM model in background...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
                logging.info("LLM model loaded successfully in background")
            except Exception as e:
                logging.error(f"Failed to load LLM model: {str(e)}")
                logging.info("Falling back to conversation algorithm only")
                self.tokenizer = None
                self.model = None
        
        # 백그라운드에서 모델 로딩
        thread = threading.Thread(target=load_model)
        thread.daemon = True
        thread.start()

    def set_db_priority_mode(self, enabled: bool):
        """DB 우선 검색 모드를 설정합니다."""
        self.use_db_priority = enabled
        if enabled and self.db is not None:
            self.search_service = MongoDBSearchService(self.db)
        else:
            self.search_service = None
        logging.info(f"DB priority mode: {'enabled' if enabled else 'disabled'}")

    async def process_message(self, message: str, conversation_id: str = None) -> str:
        """
        고객 응대 알고리즘에 따른 메시지 처리
        
        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID
            
        Returns:
            생성된 응답
        """
        start_time = time.time()
        self.response_stats['total_requests'] += 1
        
        try:
            logging.info(f"Received chat message: {message[:50]}...")
            
            # 1. 대화 유형 분류
            conversation_type = self.conversation_algorithm.classify_conversation_type(message)
            logging.info(f"Conversation type: {conversation_type}")
            
            if conversation_type == "casual":
                self.response_stats['casual_conversations'] += 1
                # 2. 일상 대화 처리 (LLaMA 3.1 8B)
                response = await self._handle_casual_conversation(message)
            else:
                self.response_stats['professional_conversations'] += 1
                # 3. 전문 상담 처리 (MongoDB + LLaMA 정리)
                response = await self._handle_professional_conversation(message)
            
            # 처리 시간 계산
            processing_time = (time.time() - start_time) * 1000
            self.response_stats['total_processing_time'] += processing_time
            self.response_stats['processing_times'].append(processing_time)
            
            if processing_time < self.response_stats['min_processing_time']:
                self.response_stats['min_processing_time'] = processing_time
            if processing_time > self.response_stats['max_processing_time']:
                self.response_stats['max_processing_time'] = processing_time
            
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] 상담사 응답 완료")
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] 처리 시간: {processing_time:.2f}ms")
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] 응답 내용: {response[:100]}...")
            
            return response
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            self.response_stats['errors'] += 1
            self.response_stats['error_processing_time'] += error_time
            
            logging.error(f"Error processing message: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    async def _handle_casual_conversation(self, message: str) -> str:
        """일상 대화 처리"""
        # 일단 기본 응답으로 안정성 확보
        return self.conversation_algorithm._generate_casual_response(message)

    async def _handle_professional_conversation(self, message: str) -> str:
        """전문 상담 처리"""
        db_start_time = time.time()
        
        try:
            # 1. MongoDB에서 관련 답변 검색
            db_answer = None
            if self.search_service:
                db_answer = await self.search_service.search_answer(message)
            
            db_time = (time.time() - db_start_time) * 1000
            self.response_stats['db_processing_time'] += db_time
            
            # 2. DB 답변이 있는 경우 기본 포맷팅 사용
            if db_answer:
                self.response_stats['db_responses'] += 1
                return self._format_db_answer(db_answer)
            else:
                # 3. DB 답변이 없는 경우 상담사 연락 안내
                return self.conversation_algorithm.generate_no_answer_response(message)
                
        except Exception as e:
            logging.error(f"Error in professional conversation: {str(e)}")
            return self.conversation_algorithm.generate_no_answer_response(message)

    def _format_response(self, response: str) -> str:
        """응답을 포맷팅합니다."""
        return FormattingService.format_response(response)

    def get_response_stats(self) -> Dict:
        """응답 시간 통계를 반환합니다."""
        stats = self.response_stats.copy()
        
        if stats['total_requests'] > 0:
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['total_requests']
            if stats['db_responses'] > 0:
                stats['avg_db_processing_time'] = stats['db_processing_time'] / stats['db_responses']
            if stats['llama_responses'] > 0:
                stats['avg_llama_processing_time'] = stats['llama_processing_time'] / stats['llama_responses']
            else:
                stats['avg_llama_processing_time'] = 0
            
            # 중간값 계산
            if stats['processing_times']:
                sorted_times = sorted(stats['processing_times'])
                stats['median_processing_time'] = sorted_times[len(sorted_times) // 2]
        else:
            stats['avg_processing_time'] = 0
            stats['avg_db_processing_time'] = 0
            stats['avg_llama_processing_time'] = 0
            stats['median_processing_time'] = 0
        
        return stats

    def log_response_stats(self):
        """응답 시간 통계를 로그로 출력합니다."""
        stats = self.get_response_stats()
        
        logging.info("=" * 60)
        logging.info("고객 응대 알고리즘 통계")
        logging.info("=" * 60)
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"일상 대화: {stats['casual_conversations']} ({stats['casual_conversations']/stats['total_requests']*100:.1f}%)")
        logging.info(f"전문 상담: {stats['professional_conversations']} ({stats['professional_conversations']/stats['total_requests']*100:.1f}%)")
        logging.info(f"DB 응답: {stats['db_responses']}")
        logging.info(f"LLaMA 응답: {stats['llama_responses']}")
        logging.info(f"오류: {stats['errors']}")
        logging.info("-" * 60)
        logging.info(f"평균 처리 시간: {stats['avg_processing_time']:.2f}ms")
        logging.info(f"중간값 처리 시간: {stats['median_processing_time']:.2f}ms")
        logging.info(f"최소 처리 시간: {stats['min_processing_time']:.2f}ms")
        logging.info(f"최대 처리 시간: {stats['max_processing_time']:.2f}ms")
        logging.info(f"평균 DB 처리 시간: {stats['avg_db_processing_time']:.2f}ms")
        
        # LLaMA 처리 시간 안전하게 출력
        avg_llama_time = stats.get('avg_llama_processing_time', 0)
        logging.info(f"평균 LLaMA 처리 시간: {avg_llama_time:.2f}ms")
        logging.info("=" * 60)

    async def _enhance_db_answer_with_llm(self, message: str, db_answer: str) -> str:
        """LLaMA 3.1 8B로 DB 답변을 개선합니다."""
        try:
            current_model = self.get_current_model()
            if not current_model:
                return self._format_db_answer(db_answer)
            
            # 간단하고 명확한 프롬프트 사용
            prompt = f"사용자 질문: {message}\n\nDB 답변: {db_answer}\n\n위 답변을 친절하고 이해하기 쉽게 정리해주세요:"
            
            model, tokenizer = current_model
            
            # 토크나이저 설정
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 모델에 직접 입력 (attention_mask 명시적 설정)
            inputs = tokenizer(
                prompt, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # 생성 (파라미터 최적화)
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=100,
                    temperature=0.6,
                    top_p=0.8,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    num_beams=1,
                    use_cache=True
                )
            
            # 응답 후처리
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            response = response.strip()
            
            # 응답이 너무 짧거나 의미없는 경우 기본 포맷팅 사용
            if len(response) < 10 or response in ["", "네", "알겠습니다", "좋습니다"]:
                return self._format_db_answer(db_answer)
            
            return response
            
        except Exception as e:
            logging.error(f"Error enhancing DB answer with LLM: {str(e)}")
            return self._format_db_answer(db_answer)

    def _format_db_answer(self, db_answer: str) -> str:
        """DB 답변을 포맷팅합니다."""
        try:
            # 기본 정리
            response = db_answer.strip()
            
            # 줄바꿈 개선
            response = response.replace('\\n', '\n')
            response = response.replace('  ', '\n')  # 두 개 이상의 공백을 줄바꿈으로
            response = response.replace('* ', '\n• ')  # 불릿 포인트 개선
            response = response.replace('1. ', '\n1. ')  # 번호 매기기 개선
            response = response.replace('2. ', '\n2. ')
            response = response.replace('3. ', '\n3. ')
            response = response.replace('4. ', '\n4. ')
            
            # 응답 길이 제한 (문자 수 기준)
            if len(response) > 300:  # 300자로 제한
                response = response[:300] + "..."
            
            # 불필요한 줄바꿈 정리
            response = '\n'.join(line.strip() for line in response.split('\n') if line.strip())
            
            # 친절한 마무리 추가
            response += "\n\n도움이 되셨나요? 다른 질문이 있으시면 언제든 말씀해 주세요."
            
            return response
            
        except Exception as e:
            logging.error(f"Error formatting DB answer: {str(e)}")
            return db_answer
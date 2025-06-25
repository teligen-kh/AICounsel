from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_mongodb import MongoDBChatMessageHistory
from ..config import settings
from .mongodb_search_service import MongoDBSearchService
from .conversation_algorithm import ConversationAlgorithm
from .formatting_service import FormattingService
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from enum import Enum

class IntentType(Enum):
    """사용자 의도 타입"""
    GREETING = "greeting"  # 인사
    QUESTION = "question"  # 질문
    COMPLAINT = "complaint"  # 불만/문제
    REQUEST = "request"  # 요청
    THANKS = "thanks"  # 감사
    UNKNOWN = "unknown"  # 알 수 없음

class LLMService:
    def __init__(self, db: AsyncIOMotorDatabase = None, use_db_priority: bool = True):
        """
        LLM 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결
            use_db_priority: DB 우선 검색 모드 사용 여부
        """
        self.db = db
        self.use_db_priority = use_db_priority
        
        # MongoDB 검색 서비스 초기화
        if db is not None and use_db_priority:
            self.search_service = MongoDBSearchService(db)
        else:
            self.search_service = None
        
        # 대화 알고리즘 초기화
        self.conversation_algorithm = ConversationAlgorithm()
        
        # 응답 시간 통계 초기화
        self.response_stats = {
            'total_requests': 0,
            'db_responses': 0,
            'algorithm_responses': 0,
            'errors': 0,
            'total_processing_time': 0,
            'db_processing_time': 0,
            'algorithm_processing_time': 0,
            'error_processing_time': 0,
            'min_processing_time': float('inf'),
            'max_processing_time': 0,
            'processing_times': []  # 모든 처리 시간 기록
        }
        
        # LLaMA 3.1 8B Instruct 모델 경로
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                "models", "Llama-3.1-8B-Instruct")
        
        # 토크나이저와 모델 로드 (비동기로 미리 로딩)
        self.tokenizer = None
        self.model = None
        self._load_model_async(model_path)

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
        메시지를 처리하고 응답을 생성합니다.
        
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
            
            # DB에서 관련 답변 검색
            db_answer = None
            if self.search_service:
                db_answer = await self.search_service.search_answer(message)
            
            # DB 답변이 있으면 바로 포맷팅해서 반환 (LLM 개선 없이)
            if db_answer:
                logging.info(f"DB answer found, formatting... Original: {db_answer[:100]}...")
                response = self._format_db_answer(db_answer)
                logging.info(f"DB answer formatted: {response[:100]}...")
                self.response_stats['db_responses'] += 1
            else:
                # 대화 알고리즘으로 응답 생성
                response = await self.conversation_algorithm.generate_response(
                    message, None, self.model, self.tokenizer
                )
                self.response_stats['algorithm_responses'] += 1
                
                # 응답 길이 제한 및 줄바꿈 개선 (알고리즘 응답에만 적용)
                response = self._format_response(response)
            
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
            if stats['algorithm_responses'] > 0:
                stats['avg_algorithm_processing_time'] = stats['algorithm_processing_time'] / stats['algorithm_responses']
            
            # 중간값 계산
            if stats['processing_times']:
                sorted_times = sorted(stats['processing_times'])
                stats['median_processing_time'] = sorted_times[len(sorted_times) // 2]
        else:
            stats['avg_processing_time'] = 0
            stats['avg_db_processing_time'] = 0
            stats['avg_algorithm_processing_time'] = 0
            stats['median_processing_time'] = 0
        
        return stats

    def log_response_stats(self):
        """응답 시간 통계를 로그로 출력합니다."""
        stats = self.get_response_stats()
        
        logging.info("=" * 60)
        logging.info("응답 시간 통계")
        logging.info("=" * 60)
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"DB 응답 수: {stats['db_responses']}")
        logging.info(f"알고리즘 응답 수: {stats['algorithm_responses']}")
        logging.info(f"오류 수: {stats['errors']}")
        logging.info("-" * 60)
        logging.info(f"평균 처리 시간: {stats['avg_processing_time']:.2f}ms")
        logging.info(f"DB 평균 처리 시간: {stats['avg_db_processing_time']:.2f}ms")
        logging.info(f"알고리즘 평균 처리 시간: {stats['avg_algorithm_processing_time']:.2f}ms")
        logging.info(f"중간값 처리 시간: {stats['median_processing_time']:.2f}ms")
        logging.info(f"최소 처리 시간: {stats['min_processing_time']:.2f}ms")
        logging.info(f"최대 처리 시간: {stats['max_processing_time']:.2f}ms")
        logging.info("=" * 60) 

    async def _enhance_db_answer_with_llm(self, message: str, db_answer: str) -> str:
        """DB 답변을 LLM으로 개선하여 더 친절하게 만듭니다."""
        try:
            # 모델이 로드되지 않은 경우 DB 답변을 간단히 정리해서 반환
            if self.model is None or self.tokenizer is None:
                logging.warning("LLM model not loaded, using formatted DB answer")
                return self._format_db_answer(db_answer)
            
            # DB 답변을 친절하게 개선하는 프롬프트
            enhancement_prompt = f"""다음은 사용자의 질문과 관련된 전문적인 답변입니다. 
이 답변을 친절하고 이해하기 쉽게 개선해주세요.

사용자 질문: {message}
전문 답변: {db_answer}

위의 전문 답변을 바탕으로 다음 조건을 만족하는 답변을 제공해주세요:
1. 친절하고 이해하기 쉬운 톤으로 작성
2. 전문 용어가 있다면 쉬운 말로 설명
3. 단계별로 명확하게 나열 (1. 2. 3. 형태)
4. 실용적이고 실행 가능한 내용만 포함
5. 한국어로 자연스럽게 작성
6. 상담사가 안내하는 느낌으로 작성
7. 줄바꿈을 적절히 사용하여 가독성 향상
8. DB 관련 용어는 "데이터베이스"로 통일
9. ARUMLOCADB는 "아루모로카 데이터베이스"로 설명
10. 각 단계마다 구체적인 설명 추가

답변은 친근하고 도움이 되는 톤으로 작성해주세요."""

            # LLaMA 3.1 8B Instruct 형식으로 입력 구성
            conversation_text = f"<|im_start|>user\n{enhancement_prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            # 모델에 직접 입력
            inputs = self.tokenizer(conversation_text, return_tensors="pt")
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=300,  # 200에서 300으로 증가
                    temperature=0.7,    # 0.6에서 0.7로 조정
                    top_p=0.9,          # 0.8에서 0.9로 조정
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,  # 1.1에서 1.2로 조정
                    no_repeat_ngram_size=3,   # n-gram 반복 방지
                    length_penalty=1.1  # 길이 페널티 추가
                )
            
            # 응답 후처리
            response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            
            # 응답 정리 및 개선
            response = response.strip()
            
            # FormattingService를 사용하여 포맷팅
            response = FormattingService.format_response(response)
            
            return response
            
        except Exception as e:
            logging.error(f"Error enhancing DB answer with LLM: {str(e)}")
            # DB 답변을 간단히 정리해서 반환
            return self._format_db_answer(db_answer)

    def _format_db_answer(self, db_answer: str) -> str:
        """DB 답변을 간단히 정리하여 반환합니다."""
        logging.info(f"Formatting DB answer: {db_answer[:100]}...")
        formatted = FormattingService.format_db_answer(db_answer)
        logging.info(f"Formatted result: {formatted[:100]}...")
        return formatted
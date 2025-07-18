from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_mongodb import MongoDBChatMessageHistory
from ..config import settings
from .mongodb_search_service import MongoDBSearchService
from .conversation_algorithm import ConversationAlgorithm
from .formatting_service import FormattingService
from .model_manager import get_model_manager, ModelType
from .llm_processors import LLMProcessorFactory, BaseLLMProcessor
from .llama_cpp_processor import LlamaCppProcessor
from .finetuned_processor import get_finetuned_processor
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
    def __init__(self, use_db_mode: bool = False, use_llama_cpp: bool = False, use_finetuned: bool = False):
        """
        순수 LLM 서비스 초기화 (DB 의존성 제거)
        
        Args:
            use_db_mode: DB 연동 모드 사용 여부 (기본값: False)
            use_llama_cpp: llama-cpp-python 사용 여부 (기본값: False)
            use_finetuned: 파인튜닝된 모델 사용 여부 (기본값: False)
        """
        self.use_db_mode = use_db_mode
        self.use_llama_cpp = use_llama_cpp
        self.use_finetuned = use_finetuned
        self.model_type = "llama-3.1-8b-instruct"  # 기본 모델
        
        # 원본 Llama-3.1-8B-Instruct 모델 직접 초기화
        self._initialize_original_llama()
        
        # DB 서비스는 외부에서 주입받음 (의존성 분리)
        self.search_service = None
        
        # 응답 시간 통계 초기화
        self.response_stats = {
            'total_requests': 0,
            'llama_responses': 0,
            'db_responses': 0,
            'errors': 0,
            'total_processing_time': 0,
            'llama_processing_time': 0,
            'db_processing_time': 0,
            'error_processing_time': 0,
            'min_processing_time': float('inf'),
            'max_processing_time': 0,
            'processing_times': []
        }

    def _initialize_original_llama(self):
        """원본 Llama-3.1-8B-Instruct 모델 직접 초기화"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # 모델 경로 설정
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                    "models", "Llama-3.1-8B-Instruct")
            
            logging.info(f"원본 Llama-3.1-8B-Instruct 모델 로딩 중: {model_path}")
            
            # 토크나이저와 모델 로드
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            logging.info("✅ 원본 Llama-3.1-8B-Instruct 모델 로딩 완료")
            
        except Exception as e:
            logging.error(f"원본 Llama 모델 초기화 실패: {str(e)}")
            raise

    def _initialize_finetuned(self):
        """파인튜닝된 모델 초기화"""
        try:
            self.finetuned_processor = get_finetuned_processor()
            logging.info("✅ 파인튜닝된 모델 초기화 완료")
        except Exception as e:
            logging.error(f"파인튜닝된 모델 초기화 실패: {str(e)}")
            raise

    def _initialize_transformers(self):
        """Transformers 기반 초기화"""
        # 모델 매니저 가져오기
        self.model_manager = get_model_manager()
        
        # 모델별 프로세서 초기화
        self.processor = LLMProcessorFactory.create_processor(self.model_type)
        logging.info(f"Transformers LLM 프로세서 초기화 완료: {self.model_type}")
        
        # 모델 로딩
        self._load_model_sync(self.model_type)

    def _initialize_llama_cpp(self):
        """llama-cpp-python 기반 초기화"""
        try:
            # GGUF 모델 경로 설정
            model_path = self._get_gguf_model_path()
            
            # llama-cpp 프로세서 초기화 (기본 스타일: 친근한 상담사)
            from .conversation_style_manager import ConversationStyle
            self.llama_cpp_processor = LlamaCppProcessor(model_path, self.model_type, ConversationStyle.FRIENDLY)
            logging.info(f"llama-cpp LLM 프로세서 초기화 완료: {self.model_type}")
            
        except Exception as e:
            logging.error(f"llama-cpp 초기화 실패: {str(e)}")
            # 폴백: transformers 사용
            logging.info("Transformers로 폴백합니다.")
            self.use_llama_cpp = False
            self._initialize_transformers()

    def _get_gguf_model_path(self) -> str:
        """GGUF 모델 경로 반환 (Phi-3.5만 체크)"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models")
        model_path = os.path.join(base_path, "Phi-3.5-mini-instruct-Q8_0.gguf")
        
        if os.path.exists(model_path):
            return model_path
        
        raise FileNotFoundError(f"GGUF model not found: {model_path}")

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
            if self.use_llama_cpp:
                # llama-cpp 모델 전환
                model_path = self._get_gguf_model_path()
                self.llama_cpp_processor.cleanup()
                self.llama_cpp_processor = LlamaCppProcessor(model_path, model_type)
                self.model_type = model_type
                logging.info(f"Switched to llama-cpp model: {model_type}")
            else:
                # transformers 모델 전환
                success = self.model_manager.switch_model(model_type)
                if success:
                    self.model_type = model_type
                    # 프로세서도 함께 전환
                    self.processor = LLMProcessorFactory.create_processor(model_type)
                    logging.info(f"Switched to transformers model: {model_type}")
                return success
            return True
        except Exception as e:
            logging.error(f"Failed to switch model: {str(e)}")
            return False
    
    def get_current_model(self):
        """현재 모델을 반환합니다."""
        if self.use_llama_cpp:
            return self.llama_cpp_processor
        else:
            return self.model_manager.get_current_model()
    
    def get_current_model_config(self):
        """현재 모델 설정을 반환합니다."""
        if self.use_llama_cpp:
            return {"type": "llama-cpp", "model_type": self.model_type}
        else:
            return self.model_manager.get_current_model_config()

    def inject_db_service(self, db_service):
        """DB 서비스를 외부에서 주입받습니다."""
        self.search_service = db_service
        logging.info("DB 서비스 주입 완료")

    def remove_db_service(self):
        """DB 서비스를 제거합니다."""
        self.search_service = None
        logging.info("DB 서비스 제거 완료")

    def set_db_mode(self, enabled: bool):
        """DB 연동 모드를 설정합니다."""
        self.use_db_mode = enabled
        logging.info(f"DB 연동 모드: {'활성화' if enabled else '비활성화'}")
    
    def set_conversation_style(self, style: str):
        """대화 스타일을 설정합니다."""
        try:
            from .conversation_style_manager import ConversationStyle
            style_enum = ConversationStyle(style)
            
            if self.use_llama_cpp and self.llama_cpp_processor:
                # 새로운 스타일로 프로세서 재초기화
                model_path = self._get_gguf_model_path()
                self.llama_cpp_processor.cleanup()
                self.llama_cpp_processor = LlamaCppProcessor(model_path, self.model_type, style_enum)
                logging.info(f"대화 스타일 변경됨: {style}")
            else:
                logging.warning("llama-cpp가 활성화되지 않아 스타일 변경이 불가능합니다.")
                
        except ValueError:
            logging.error(f"지원하지 않는 스타일: {style}")
        except Exception as e:
            logging.error(f"스타일 변경 중 오류: {str(e)}")

    async def process_message(self, message: str, conversation_id: str = None) -> str:
        """
        모듈화된 메시지 처리 (DB 모드/순수 LLM 모드 자동 선택)
        
        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID
            
        Returns:
            str: 처리된 응답
        """
        start_time = time.time()
        self.response_stats['total_requests'] += 1
        
        try:
            # DB 모드가 활성화되고 DB 서비스가 있으면 DB 연동 처리
            if self.use_db_mode and self.search_service:
                response = await self._handle_db_enhanced_message(message)
            else:
                # 순수 LLM 모드: 원본 모델만 사용
                response = await self._handle_pure_llm_message(message)
            
            # 응답 포맷팅
            formatted_response = await self.format_and_send_response(response)
            
            # 통계 업데이트
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # ms
            self._update_stats(processing_time, True)
            
            return formatted_response
            
        except Exception as e:
            logging.error(f"메시지 처리 중 오류 발생: {str(e)}")
            self.response_stats['errors'] += 1
            
            # 오류 처리 시간 기록
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            self._update_stats(processing_time, False)
            
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    async def _handle_pure_llm_message(self, message: str) -> str:
        """순수 LLM 모드: 원본 모델만 사용"""
        logging.info("순수 LLM 모드로 메시지 처리")
        return await self._handle_transformers_casual(message)

    async def _handle_db_enhanced_message(self, message: str) -> str:
        """DB 연동 모드: DB 검색 + LLM 강화"""
        logging.info("DB 연동 모드로 메시지 처리")
        
        try:
            # 1. DB에서 관련 답변 검색
            db_start_time = time.time()
            db_answer = await self.search_service.search_answer(message)
            db_end_time = time.time()
            db_processing_time = (db_end_time - db_start_time) * 1000
            
            self.response_stats['db_processing_time'] += db_processing_time
            
            if db_answer:
                self.response_stats['db_responses'] += 1
                logging.info(f"DB에서 답변 찾음: {db_answer[:100]}...")
                
                # 2. LLM으로 답변 강화
                enhanced_answer = await self._enhance_db_answer_with_llm(message, db_answer)
                return enhanced_answer
            else:
                logging.info("DB에서 관련 답변을 찾지 못함")
                # DB에서 답변을 찾지 못한 경우 순수 LLM으로 처리
                return await self._handle_pure_llm_message(message)
                
        except Exception as e:
            logging.error(f"DB 연동 처리 중 오류: {str(e)}")
            # 오류 발생 시 순수 LLM으로 폴백
            return await self._handle_pure_llm_message(message)

    async def get_conversation_response(self, message: str) -> str:
        """
        대화 응답 생성 (파인튜닝된 모델 우선)
        
        Args:
            message: 사용자 메시지
            
        Returns:
            str: 생성된 응답
        """
        try:
            # 파인튜닝된 모델 우선 사용
            if self.use_finetuned and hasattr(self, 'finetuned_processor') and self.finetuned_processor:
                return await self._handle_finetuned_casual(message)
            elif self.use_llama_cpp:
                return await self._handle_llama_cpp_casual(message)
            else:
                return await self._handle_transformers_casual(message)
        except Exception as e:
            logging.error(f"대화 응답 생성 중 오류: {str(e)}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."

    async def _handle_finetuned_casual(self, message: str) -> str:
        """파인튜닝된 모델로 일상 대화 처리"""
        try:
            if hasattr(self, 'finetuned_processor') and self.finetuned_processor:
                # 파인튜닝된 모델로 응답 생성
                prompt = f"사용자: {message}\n상담사:"
                response = self.finetuned_processor.generate_response(prompt, max_length=256, temperature=0.7)
                self.response_stats['finetuned_responses'] += 1
                return response
            else:
                # 폴백: 기본 모델 사용
                return await self._handle_llama_cpp_casual(message)
        except Exception as e:
            logging.error(f"파인튜닝된 모델 응답 생성 실패: {str(e)}")
            # 폴백: 기본 모델 사용
            return await self._handle_llama_cpp_casual(message)

    async def _handle_llama_cpp_casual(self, message: str) -> str:
        """llama-cpp를 사용한 일상 대화 처리"""
        try:
            # 입력 필터 처리 (욕설, 비상담 질문 체크)
            template_response, use_template = self.llama_cpp_processor.process_user_input(message)
            
            if use_template:
                # 템플릿 응답 사용 (욕설, 비상담 질문)
                self.response_stats['llama_responses'] += 1
                return template_response
            
            # 일반적인 경우 LLM 처리
            prompt = self.llama_cpp_processor.create_casual_prompt(message)
            response = self.llama_cpp_processor.generate_response(prompt)
            
            if response:
                self.response_stats['llama_responses'] += 1
                return response
            else:
                return "죄송합니다. 적절한 응답을 생성하지 못했습니다."
                
        except Exception as e:
            logging.error(f"llama-cpp 일상 대화 처리 오류: {str(e)}")
            return "죄송합니다. 응답 생성 중 오류가 발생했습니다."

    async def _handle_transformers_casual(self, message: str) -> str:
        """원본 Llama-3.1-8B-Instruct 모델을 사용한 일상 대화 처리 (Hugging Face 공식 방식)"""
        try:
            # Hugging Face 공식 chat template 사용
            messages = [
                {"role": "user", "content": message}
            ]
            
            # 공식 chat template 적용
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            # 토크나이징
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            
            # Hugging Face 최적화 파라미터 사용
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=1024,       # 더 긴 응답 허용 (512 -> 1024)
                    temperature=0.7,           # 적당한 창의성
                    top_p=0.9,                 # nucleus sampling
                    do_sample=True,            # 샘플링 활성화
                    repetition_penalty=1.1,    # 반복 방지
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 응답 디코딩 (공식 방식)
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 사용자 프롬프트 제거하고 어시스턴트 응답만 추출
            # Hugging Face 공식 chat template 형식에 맞춰 처리
            if "<|im_start|>assistant" in response:
                assistant_response = response.split("<|im_start|>assistant")[-1].strip()
            elif "assistant" in response:
                # 다른 형식의 assistant 태그 처리
                assistant_response = response.split("assistant")[-1].strip()
            else:
                # 프롬프트 제거
                assistant_response = response.replace(formatted_prompt, "").strip()
            
            # 특수 토큰 제거
            assistant_response = assistant_response.replace("<|im_end|>", "").replace("<|im_start|>", "")
            assistant_response = assistant_response.replace("<|endoftext|>", "")
            
            if assistant_response:
                self.response_stats['llama_responses'] += 1
                return assistant_response
            else:
                return "죄송합니다. 적절한 응답을 생성하지 못했습니다."
                
        except Exception as e:
            logging.error(f"원본 Llama 일상 대화 처리 오류: {str(e)}")
            return "죄송합니다. 응답 생성 중 오류가 발생했습니다."

    async def search_and_enhance_answer(self, message: str) -> str:
        """
        DB 검색 후 LLM으로 답변 강화
        
        Args:
            message: 사용자 메시지
            
        Returns:
            str: 강화된 답변
        """
        if not self.search_service:
            logging.warning("Search service not available")
            return await self.get_conversation_response(message)
        
        try:
            # 1. DB에서 관련 답변 검색
            db_start_time = time.time()
            db_answer = await self.search_service.search_answer(message)
            db_end_time = time.time()
            db_processing_time = (db_end_time - db_start_time) * 1000
            
            self.response_stats['db_processing_time'] += db_processing_time
            
            if db_answer:
                self.response_stats['db_responses'] += 1
                logging.info(f"DB에서 답변 찾음: {db_answer[:100]}...")
                
                # 2. LLM으로 답변 강화
                enhanced_answer = await self._enhance_db_answer_with_llm(message, db_answer)
                return enhanced_answer
            else:
                logging.info("DB에서 관련 답변을 찾지 못함")
                # DB에서 답변을 찾지 못한 경우 일반 대화로 처리
                return await self.get_conversation_response(message)
                
        except Exception as e:
            logging.error(f"DB 검색 및 강화 중 오류: {str(e)}")
            # 오류 발생 시 일반 대화로 폴백
            return await self.get_conversation_response(message)

    async def format_and_send_response(self, response: str) -> str:
        """응답 포맷팅 및 전송"""
        try:
            # 기본 포맷팅
            formatted_response = self._format_response(response)
            
            # 추가 포맷팅 서비스 사용
            formatting_service = FormattingService()
            final_response = formatting_service.format_response(formatted_response)
            
            return final_response
            
        except Exception as e:
            logging.error(f"응답 포맷팅 중 오류: {str(e)}")
            return response

    async def _handle_casual_conversation(self, message: str) -> str:
        """일상 대화 처리"""
        return await self.get_conversation_response(message)

    async def _handle_professional_conversation(self, message: str) -> str:
        """전문 상담 처리"""
        return await self.search_and_enhance_answer(message)

    async def _enhance_db_answer_with_llm(self, message: str, db_answer: str) -> str:
        """DB 답변을 원본 Llama-3.1-8B-Instruct 모델로 강화"""
        try:
            # LLaMA 형식 프롬프트
            formatted_prompt = f"""<|im_start|>user
사용자 질문: {message}

DB 답변: {db_answer}

위 답변을 친절하고 이해하기 쉽게 정리해주세요.<|im_end|>
<|im_start|>assistant
"""
            
            # 토크나이징
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 응답 디코딩
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 사용자 프롬프트 제거하고 어시스턴트 응답만 추출
            if "<|im_start|>assistant" in response:
                assistant_response = response.split("<|im_start|>assistant")[-1].strip()
            else:
                assistant_response = response.replace(formatted_prompt, "").strip()
            
            # LLaMA 특수 토큰 제거
            assistant_response = assistant_response.replace("<|im_end|>", "").replace("<|im_start|>", "")
            
            if assistant_response:
                self.response_stats['llama_responses'] += 1
                return assistant_response
            
            # LLM 강화 실패 시 DB 답변 그대로 반환
            return self._format_db_answer(db_answer)
                
        except Exception as e:
            logging.error(f"DB 답변 LLM 강화 중 오류: {str(e)}")
            # 오류 발생 시 DB 답변 그대로 반환
            return self._format_db_answer(db_answer)

    def _format_db_answer(self, db_answer: str) -> str:
        """DB 답변 포맷팅"""
        try:
            # 기본 정리
            formatted = db_answer.strip()
            
            # 불필요한 문자 제거
            formatted = re.sub(r'\s+', ' ', formatted)  # 연속된 공백을 하나로
            
            # 길이 제한
            if len(formatted) > 1000:
                formatted = formatted[:1000] + "..."
            
            return formatted
            
        except Exception as e:
            logging.error(f"DB 답변 포맷팅 중 오류: {str(e)}")
            return db_answer

    def _format_response(self, response: str) -> str:
        """응답 포맷팅"""
        if not response:
            return "죄송합니다. 응답을 생성하지 못했습니다."
        
        # 기본 정리
        response = response.strip()
        
        # 길이 제한 (300 -> 1000으로 증가)
        if len(response) > 1000:
            response = response[:1000] + "..."
        
        return response

    def _update_stats(self, processing_time: float, success: bool):
        """통계 업데이트"""
        self.response_stats['total_processing_time'] += processing_time
        self.response_stats['processing_times'].append(processing_time)
        
        # 최소/최대 처리 시간 업데이트
        if processing_time < self.response_stats['min_processing_time']:
            self.response_stats['min_processing_time'] = processing_time
        if processing_time > self.response_stats['max_processing_time']:
            self.response_stats['max_processing_time'] = processing_time
        
        if not success:
            self.response_stats['error_processing_time'] += processing_time

    def get_response_stats(self) -> Dict:
        """응답 통계 반환"""
        stats = self.response_stats.copy()
        
        # 평균 처리 시간 계산
        if stats['processing_times']:
            stats['avg_processing_time'] = sum(stats['processing_times']) / len(stats['processing_times'])
        else:
            stats['avg_processing_time'] = 0
        
        # 성공률 계산
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['total_requests'] - stats['errors']) / stats['total_requests'] * 100
        else:
            stats['success_rate'] = 0
        
        return stats

    def log_response_stats(self):
        """응답 통계 로깅"""
        stats = self.get_response_stats()
        
        logging.info("=== LLM 서비스 응답 통계 ===")
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"일상 대화: {stats['casual_conversations']}")
        logging.info(f"전문 상담: {stats['professional_conversations']}")
        logging.info(f"DB 응답: {stats['db_responses']}")
        logging.info(f"LLM 응답: {stats['llama_responses']}")
        logging.info(f"오류: {stats['errors']}")
        logging.info(f"성공률: {stats['success_rate']:.1f}%")
        logging.info(f"평균 처리 시간: {stats['avg_processing_time']:.2f}ms")
        logging.info(f"최소 처리 시간: {stats['min_processing_time']:.2f}ms")
        logging.info(f"최대 처리 시간: {stats['max_processing_time']:.2f}ms")
        logging.info(f"총 처리 시간: {stats['total_processing_time']:.2f}ms")
        logging.info(f"DB 처리 시간: {stats['db_processing_time']:.2f}ms")
        logging.info(f"LLM 처리 시간: {stats['llama_processing_time']:.2f}ms")
        logging.info(f"오류 처리 시간: {stats['error_processing_time']:.2f}ms")
        logging.info("================================")
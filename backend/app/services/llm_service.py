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
    def __init__(self, db: AsyncIOMotorDatabase = None, use_db_priority: bool = True, model_type: str = ModelType.POLYGLOT_KO_5_8B.value, use_llama_cpp: bool = False):
        """
        LLM 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결
            use_db_priority: DB 우선 검색 모드 사용 여부
            model_type: 사용할 모델 타입
            use_llama_cpp: llama-cpp-python 사용 여부
        """
        self.db = db
        self.use_db_priority = use_db_priority
        self.model_type = model_type  # 서버 시작 시 설정된 모델 타입
        self.use_llama_cpp = use_llama_cpp
        
        # llama-cpp 사용 여부에 따른 초기화
        if use_llama_cpp:
            self._initialize_llama_cpp()
        else:
            self._initialize_transformers()
        
        # MongoDB 검색 서비스 초기화 (비동기로 처리)
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
            
            # llama-cpp 프로세서 초기화
            self.llama_cpp_processor = LlamaCppProcessor(model_path, self.model_type)
            logging.info(f"llama-cpp LLM 프로세서 초기화 완료: {self.model_type}")
            
        except Exception as e:
            logging.error(f"llama-cpp 초기화 실패: {str(e)}")
            # 폴백: transformers 사용
            logging.info("Transformers로 폴백합니다.")
            self.use_llama_cpp = False
            self._initialize_transformers()

    def _get_gguf_model_path(self) -> str:
        """GGUF 모델 경로 반환"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models")
        
        # 모델별 GGUF 파일 경로
        gguf_paths = {
            "polyglot-ko-5.8b": os.path.join(base_path, "polyglot-ko-5.8b-Q4_K_M.gguf"),
            "llama-3.1-8b": os.path.join(base_path, "llama-3.1-8b-instruct-Q4_K_M.gguf"),
            "llama-2-7b-chat": os.path.join(base_path, "llama-2-7b-chat.Q4_K_M.gguf")
        }
        
        # 현재 모델에 해당하는 GGUF 파일 확인
        if self.model_type in gguf_paths:
            path = gguf_paths[self.model_type]
            if os.path.exists(path):
                return path
        
        # 기본값: 기존 llama-2-7b-chat 사용
        default_path = gguf_paths["llama-2-7b-chat"]
        if os.path.exists(default_path):
            logging.warning(f"Requested model {self.model_type} not found, using default: {default_path}")
            return default_path
        
        raise FileNotFoundError(f"No GGUF model found for {self.model_type}")

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
                # 2. 일상 대화 처리
                response = await self._handle_casual_conversation(message)
            else:
                self.response_stats['professional_conversations'] += 1
                # 3. 전문 상담 처리
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

    # ===== 업무별 메서드 분리 =====

    async def get_conversation_response(self, message: str) -> str:
        """대화 정보 받기 - 일상 대화 처리"""
        try:
            logging.info(f"=== LLM 일상 대화 디버깅 시작 ===")
            logging.info(f"입력 메시지: {message}")
            
            if self.use_llama_cpp:
                # llama-cpp 사용
                return await self._handle_llama_cpp_casual(message)
            else:
                # transformers 사용
                return await self._handle_transformers_casual(message)
                
        except Exception as e:
            logging.error(f"Error in get_conversation_response: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다."

    async def _handle_llama_cpp_casual(self, message: str) -> str:
        """llama-cpp를 사용한 일상 대화 처리"""
        try:
            logging.info("✅ llama-cpp 모델 사용")
            
            # 프롬프트 생성
            prompt = self.llama_cpp_processor.create_casual_prompt(message)
            logging.info(f"생성된 프롬프트: {prompt[:100]}...")
            
            # 응답 생성
            response = self.llama_cpp_processor.generate_response(prompt)
            
            if response:
                logging.info(f"✅ llama-cpp 응답 생성 완료: {response[:100]}...")
                return response
            else:
                logging.warning("llama-cpp 응답이 비어있음, 기본 응답 사용")
                return "안녕하세요! 무엇을 도와드릴까요?"
                
        except Exception as e:
            logging.error(f"llama-cpp 처리 오류: {str(e)}")
            return "안녕하세요! 무엇을 도와드릴까요?"

    async def _handle_transformers_casual(self, message: str) -> str:
        """transformers를 사용한 일상 대화 처리"""
        try:
            current_model = self.get_current_model()
            if current_model:
                logging.info("✅ transformers 모델 로딩 확인됨")
                llm_start = time.time()
                model, tokenizer = current_model
                
                # 모델별 프롬프트 생성
                prompt = self.processor.create_casual_prompt(message)
                logging.info(f"생성된 프롬프트: {prompt[:100]}...")
                
                # 토크나이저 설정 (Polyglot-Ko 공식 설정)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token  # <|endoftext|>
                logging.info("✅ 토크나이저 설정 완료")
                
                # 입력 인코딩 (token_type_ids 제거)
                inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
                # Polyglot-Ko가 지원하지 않는 token_type_ids 제거
                if 'token_type_ids' in inputs:
                    del inputs['token_type_ids']
                logging.info(f"✅ 입력 인코딩 완료: {inputs['input_ids'].shape}")
                
                # 생성 파라미터 가져오기
                generation_params = self.processor.get_optimized_parameters()
                logging.info(f"✅ 생성 파라미터 설정: {generation_params}")
                
                # 모델 추론
                with torch.no_grad():
                    outputs = model.generate(
                        inputs.input_ids,
                        attention_mask=inputs.attention_mask,
                        **generation_params
                    )
                
                llm_end = time.time()
                llm_time = (llm_end - llm_start) * 1000
                logging.info(f"✅ 모델 추론 완료: {llm_time:.2f}ms")
                
                # 응답 디코딩
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                logging.info(f"✅ 응답 디코딩 완료: {generated_text[:100]}...")
                
                # 프롬프트 제거하여 실제 응답만 추출
                response = generated_text[len(prompt):].strip()
                logging.info(f"✅ 프롬프트 제거 후 응답: {response[:100]}...")
                
                # 후처리
                processed_response = self.processor.process_response(response)
                logging.info(f"✅ 후처리 완료: {processed_response[:100]}...")
                
                if processed_response:
                    self.response_stats['llama_responses'] += 1
                    self.response_stats['llama_processing_time'] += llm_time
                    return processed_response
                else:
                    logging.warning("후처리 후 응답이 비어있음, 기본 응답 사용")
                    return "안녕하세요! 무엇을 도와드릴까요?"
            else:
                logging.error("❌ 모델이 로딩되지 않음")
                return "안녕하세요! 무엇을 도와드릴까요?"
                
        except Exception as e:
            logging.error(f"transformers 처리 오류: {str(e)}")
            return "안녕하세요! 무엇을 도와드릴까요?"

    async def search_and_enhance_answer(self, message: str) -> str:
        """응답 찾기 - 전문 상담 처리 (LLM 전용)"""
        try:
            logging.info(f"=== LLM 전문 상담 디버깅 시작 ===")
            logging.info(f"입력 메시지: {message}")
            
            current_model = self.get_current_model()
            if not current_model:
                logging.error("❌ 모델이 로딩되지 않음")
                return self.conversation_algorithm.generate_no_answer_response(message)
            
            logging.info("✅ 모델 로딩 확인됨")
            
            # 모델별 프롬프트 생성
            prompt = self.processor.create_professional_prompt(message, "")
            logging.info(f"생성된 프롬프트: {prompt[:100]}...")
            
            model, tokenizer = current_model
            
            # 토크나이저 설정 (Polyglot-Ko 공식 설정)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token  # <|endoftext|>
            logging.info("✅ 토크나이저 설정 완료")
            
            # 모델에 직접 입력 (token_type_ids 제거)
            logging.info("토크나이저 처리 시작...")
            inputs = tokenizer(
                prompt, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            # Polyglot-Ko가 지원하지 않는 token_type_ids 제거
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            logging.info(f"✅ 토크나이저 처리 완료 - 입력 shape: {inputs.input_ids.shape}")
            
            # 모델별 최적화된 파라미터 사용 (더 보수적으로)
            params = self.processor.get_optimized_parameters()
            params['max_new_tokens'] = 50  # 더 짧게
            params['temperature'] = 0.1    # 더 낮게
            logging.info(f"생성 파라미터: {params}")
            
            # 성능 모니터링 시작
            generation_start = time.time()
            prompt_length = inputs.input_ids.shape[1]
            logging.info(f"생성 시작 - 프롬프트 길이: {prompt_length}")
            
            # 생성
            logging.info("모델 생성 시작...")
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    **params
                )
            logging.info(f"✅ 모델 생성 완료 - 출력 shape: {outputs.shape}")
            
            # 성능 모니터링 종료
            generation_end = time.time()
            
            # outputs가 텐서인지 튜플인지 확인
            if hasattr(outputs, 'shape'):
                # outputs가 텐서인 경우
                response_length = outputs.shape[1] - prompt_length
                logging.info(f"생성된 토큰 수: {response_length}")
            else:
                # outputs가 튜플인 경우
                response_length = outputs[0].shape[1] - prompt_length
                logging.info(f"생성된 토큰 수: {response_length}")
            
            # 성능 메트릭 로깅
            self.processor.log_performance_metrics(generation_start, generation_end, prompt_length, response_length)
            
            # 응답 후처리
            logging.info("응답 디코딩 시작...")
            try:
                # outputs가 텐서인지 튜플인지 확인
                if hasattr(outputs, 'shape'):
                    # outputs가 텐서인 경우
                    logging.info(f"✅ outputs는 텐서입니다 - shape: {outputs.shape}")
                    logging.info(f"입력 토큰 수: {inputs.input_ids.shape[1]}")
                    logging.info(f"전체 출력 토큰 수: {outputs.shape[1]}")
                    
                    # 생성된 토큰만 추출
                    generated_tokens = outputs[0, inputs.input_ids.shape[1]:]
                    logging.info(f"생성된 토큰 shape: {generated_tokens.shape}")
                    logging.info(f"생성된 토큰 내용: {generated_tokens.tolist()}")
                    
                    # 디코딩
                    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
                    logging.info(f"✅ 디코딩 완료 - 원본 응답: '{response}'")
                    logging.info(f"응답 길이: {len(response)}")
                else:
                    # outputs가 튜플인 경우
                    logging.info(f"✅ outputs는 튜플입니다 - 길이: {len(outputs)}")
                    logging.info(f"입력 토큰 수: {inputs.input_ids.shape[1]}")
                    logging.info(f"전체 출력 토큰 수: {outputs[0].shape[1]}")
                    
                    # 생성된 토큰만 추출
                    generated_tokens = outputs[0][0, inputs.input_ids.shape[1]:]
                    logging.info(f"생성된 토큰 shape: {generated_tokens.shape}")
                    logging.info(f"생성된 토큰 내용: {generated_tokens.tolist()}")
                    
                    # 디코딩
                    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
                    logging.info(f"✅ 디코딩 완료 - 원본 응답: '{response}'")
                    logging.info(f"응답 길이: {len(response)}")
            except Exception as decode_error:
                logging.error(f"❌ 디코딩 오류: {str(decode_error)}")
                logging.error(f"outputs type: {type(outputs)}")
                logging.error(f"outputs shape: {outputs.shape if hasattr(outputs, 'shape') else 'N/A'}")
                logging.error(f"inputs.input_ids.shape[1]: {inputs.input_ids.shape[1]}")
                import traceback
                logging.error(f"상세 오류: {traceback.format_exc()}")
                raise decode_error
            
            logging.info("응답 후처리 시작...")
            response = self.processor.process_response(response)
            logging.info(f"✅ 후처리 완료 - 최종 응답: {response}")
            
            # 응답이 너무 짧거나 의미없는 경우 기본 포맷팅 사용 (완화)
            if len(response) < 3 or response in ["", "네", "알겠습니다", "좋습니다"]:
                logging.warning(f"❌ 응답이 너무 짧거나 의미없음: '{response}'")
                return self.conversation_algorithm.generate_no_answer_response(message)
            
            logging.info(f"✅ LLM 전문 상담 처리 성공")
            return response
            
        except Exception as e:
            logging.error(f"❌ LLM 전문 상담 처리 실패: {str(e)}")
            import traceback
            logging.error(f"상세 오류: {traceback.format_exc()}")
            return self.conversation_algorithm.generate_no_answer_response(message)

    async def format_and_send_response(self, response: str) -> str:
        """응답 정보 보내기 - 응답 포맷팅"""
        try:
            # 기본 포맷팅
            formatted_response = self._format_db_answer(response)
            return formatted_response
        except Exception as e:
            logging.error(f"Error formatting response: {str(e)}")
            return response

    # ===== 기존 메서드들 (리팩토링) =====

    async def _handle_casual_conversation(self, message: str) -> str:
        """일상 대화 처리 - 업무별 메서드 호출"""
        return await self.get_conversation_response(message)

    async def _handle_professional_conversation(self, message: str) -> str:
        """전문 상담 처리 - 업무별 메서드 호출"""
        return await self.search_and_enhance_answer(message)

    async def _enhance_db_answer_with_llm(self, message: str, db_answer: str) -> str:
        """LLM으로 DB 답변을 개선합니다."""
        try:
            current_model = self.get_current_model()
            if not current_model:
                return self._format_db_answer(db_answer)
            
            # 모델별 프롬프트 생성
            prompt = self.processor.create_professional_prompt(message, db_answer)
            
            model, tokenizer = current_model
            
            # 토크나이저 설정
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 모델에 직접 입력
            inputs = tokenizer(
                prompt, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # 모델별 최적화된 파라미터 사용
            params = self.processor.get_optimized_parameters()
            params['max_new_tokens'] = 100  # 전문 상담은 더 긴 응답
            
            # 성능 모니터링 시작
            generation_start = time.time()
            prompt_length = inputs.input_ids.shape[1]
            
            # 생성
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    **params
                )
            
            # 성능 모니터링 종료
            generation_end = time.time()
            response_length = outputs[0].shape[1] - prompt_length
            
            # 성능 메트릭 로깅
            self.processor.log_performance_metrics(generation_start, generation_end, prompt_length, response_length)
            
            # 응답 후처리
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            response = self.processor.process_response(response)
            
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
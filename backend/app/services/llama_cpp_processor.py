from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time
import psutil
import re
from llama_cpp import Llama
import os
from .conversation_style_manager import get_style_manager, ConversationStyle
from .input_filter import get_input_filter, InputType

class LlamaCppProcessor:
    """llama-cpp-python을 사용하는 LLM 프로세서"""
    
    def __init__(self, model_path: str, model_type: str = "polyglot-ko-5.8b", style: ConversationStyle = ConversationStyle.FRIENDLY):
        self.model_type = model_type
        self.model_path = model_path
        self.llm = None
        self.style_manager = get_style_manager()
        self.input_filter = get_input_filter()
        self.current_style = style
        self._initialize_model()
        
    def _initialize_model(self):
        """llama-cpp 모델 초기화"""
        try:
            logging.info(f"Initializing llama-cpp model: {self.model_path}")
            
            # 모델 존재 확인
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            # llama-cpp 모델 초기화
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=2048,           # 컨텍스트 길이
                n_threads=8,          # CPU 스레드 수
                n_gpu_layers=0,       # CPU 모드 (GPU 사용 시 1 이상)
                verbose=False,        # 로그 최소화
                seed=42              # 재현 가능성
            )
            
            logging.info(f"✅ llama-cpp model initialized successfully: {self.model_type}")
            
        except Exception as e:
            logging.error(f"Failed to initialize llama-cpp model: {str(e)}")
            raise
    
    def create_casual_prompt(self, message: str) -> str:
        """일상 대화용 프롬프트 생성"""
        # 스타일 매니저에서 시스템 프롬프트 가져오기
        system_prompt = self.style_manager.get_system_prompt(self.current_style)
        
        return f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{message}<|end|>\n<|assistant|>\n"
    
    def process_user_input(self, message: str) -> tuple[str, bool]:
        """사용자 입력 처리 및 필터링"""
        # 입력 분류
        input_type, details = self.input_filter.classify_input(message)
        
        # 욕설이나 비상담 질문인 경우 템플릿 응답 반환
        if input_type in [InputType.PROFANITY, InputType.NON_COUNSELING]:
            template_response = self.input_filter.get_response_template(
                input_type, 
                self.style_manager.company_name
            )
            return template_response, True  # True = 템플릿 응답 사용
        
        # 일반적인 경우 LLM 처리
        return "", False  # False = LLM 처리 필요
    
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성"""
        # 스타일 매니저에서 시스템 프롬프트 가져오기
        system_prompt = self.style_manager.get_system_prompt(self.current_style)
        
        # 전문 상담용 추가 지시사항
        professional_instruction = "\n\n전문 상담 규칙:\n1. 제공된 참고자료의 정보만을 바탕으로 답변하세요.\n2. 참고자료에 없는 정보는 '해당 정보는 참고자료에 없습니다'라고 답변하세요."
        
        full_system_prompt = system_prompt + professional_instruction
        
        return f"<|system|>\n{full_system_prompt}<|end|>\n<|user|>\n{message}\n\n참고자료: {db_answer}\n\n위 참고자료를 바탕으로 정확한 답변을 제공해주세요.<|end|>\n<|assistant|>\n"
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """llama-cpp 최적화 파라미터 (스타일별로 조정)"""
        # 스타일 매니저에서 파라미터 가져오기
        style_params = self.style_manager.get_parameters(self.current_style)
        
        return {
            "max_tokens": 100,       # 더 긴 응답 허용 (자연스러운 대화)
            "temperature": 0.7,      # 창의성 증가 (더 자연스러운 대화)
            "top_p": 0.9,            # 상위 90% 토큰 고려 (다양성 증가)
            "top_k": 40,             # 상위 40개 토큰 (창의성 증가)
            "repeat_penalty": 1.1,   # 반복 최소화 (자연스러움)
            "stop": ["<|user|>", "<|end|>", "<|system|>"]  # Phi-3.5 중단 토큰
        }
    
    def generate_response(self, prompt: str) -> str:
        """llama-cpp를 사용한 응답 생성"""
        try:
            if not self.llm:
                raise RuntimeError("Model not initialized")
            
            start_time = time.time()
            
            # 생성 파라미터 가져오기
            params = self.get_optimized_parameters()
            
            # 응답 생성
            response = self.llm(
                prompt,
                **params
            )
            
            end_time = time.time()
            
            # 성능 로깅
            self.log_performance_metrics(start_time, end_time, len(prompt), len(response.get('choices', [{}])[0].get('text', '')))
            
            # 응답 추출
            generated_text = response.get('choices', [{}])[0].get('text', '').strip()
            
            # 후처리
            processed_text = self.process_response(generated_text)
            
            return processed_text
            
        except Exception as e:
            logging.error(f"Error generating response with llama-cpp: {str(e)}")
            return ""
    
    def process_response(self, response: str) -> str:
        """응답 후처리 - 최소한의 필터링만 적용"""
        if not response:
            return ""
        
        # 기본 정리만
        response = response.strip()
        
        # 길이 제한만
        if len(response) > 300:
            response = response[:300] + "..."
        
        return response
    
    def log_performance_metrics(self, start_time: float, end_time: float, prompt_length: int, response_length: int):
        """성능 메트릭 로깅"""
        processing_time = (end_time - start_time) * 1000  # ms
        
        # 시스템 리소스 정보
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        logging.info(f"=== llama-cpp 성능 메트릭 ===")
        logging.info(f"모델: {self.model_type}")
        logging.info(f"처리 시간: {processing_time:.2f}ms")
        logging.info(f"프롬프트 길이: {prompt_length} 문자")
        logging.info(f"응답 길이: {response_length} 문자")
        logging.info(f"문자당 처리 시간: {processing_time/max(response_length, 1):.2f}ms/char")
        logging.info(f"CPU 사용률: {cpu_percent:.1f}%")
        logging.info(f"메모리 사용률: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)")
        logging.info(f"================================")
    
    def cleanup(self):
        """리소스 정리"""
        if self.llm:
            del self.llm
            self.llm = None
            logging.info("llama-cpp model cleaned up") 
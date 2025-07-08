from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time
import psutil
import re
from llama_cpp import Llama
import os

class LlamaCppProcessor:
    """llama-cpp-python을 사용하는 LLM 프로세서"""
    
    def __init__(self, model_path: str, model_type: str = "polyglot-ko-5.8b"):
        self.model_type = model_type
        self.model_path = model_path
        self.llm = None
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
        # LLaMA 2 Chat 공식 형식
        return f"<s>[INST] {message} [/INST]"
    
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성"""
        return f"<s>[INST] {message}\n\n참고자료: {db_answer}\n\n위 참고자료를 바탕으로 답변해주세요. [/INST]"
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """llama-cpp 최적화 파라미터"""
        return {
            "max_tokens": 100,        # 적당한 길이
            "temperature": 0.6,       # 적당한 창의성
            "top_p": 0.9,            # 기본값
            "top_k": 50,             # 기본값
            "repeat_penalty": 1.1,   # 반복 방지
            "stop": ["[INST]", "</s>"]  # LLaMA 2 Chat 중단 토큰
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
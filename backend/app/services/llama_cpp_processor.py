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
        if self.model_type == "polyglot-ko-5.8b":
            # Polyglot-Ko 단순 텍스트 완성 형식
            return f"사용자: {message}\n답변:"
        else:
            # 기본 형식
            return f"사용자: {message}\n상담사:"
    
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성"""
        if self.model_type == "polyglot-ko-5.8b":
            return f"질문: {message}\n참고자료: {db_answer}\n답변:"
        else:
            return f"사용자 질문: {message}\n\nDB 답변: {db_answer}\n\n위 답변을 친절하게 정리해주세요.\n상담사:"
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """llama-cpp 최적화 파라미터"""
        if self.model_type == "polyglot-ko-5.8b":
            return {
                "max_tokens": 50,        # 최대 토큰 수
                "temperature": 0.5,      # 창의성 조절
                "top_p": 0.7,           # 누적 확률 임계값
                "top_k": 40,            # 상위 k개 토큰만 고려
                "repeat_penalty": 1.1,  # 반복 방지
                "stop": ["\n\n", "사용자:", "질문:"]  # 중단 토큰
            }
        else:
            return {
                "max_tokens": 100,
                "temperature": 0.6,
                "top_p": 0.8,
                "top_k": 50,
                "repeat_penalty": 1.1,
                "stop": ["\n\n", "사용자:", "질문:"]
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
        """응답 후처리"""
        if not response:
            return ""
        
        # 기본 정리
        response = response.strip()
        
        # Polyglot-Ko 특화 필터링
        if self.model_type == "polyglot-ko-5.8b":
            # 무의미한 패턴 필터링
            meaningless_patterns = [
                r'※.*발생하고 있습니다',
                r'안녕하세용~',
                r'ㅎㅎ',
                r'맛집.*소개',
                r'노라.*노라',
                r'잖습니까\?.*잖습니까\?',
                r'[A-Za-z]+\s+\d+:\d+\|facebook',
                r'rqproduct:\d+',
                r'-->.*\(토론\)',
                r'\d{4}년\s+\d{1,2}월\s+\d{1,2}일',
                r'\(KST\)',
                r'[가-힣]{1,2}라고.*[가-힣]{1,2}라고',
                r'[가-힣]{1,2}요\?.*[가-힣]{1,2}요\?',
            ]
            
            for pattern in meaningless_patterns:
                if re.search(pattern, response):
                    return ""
            
            # 키워드 필터링
            filter_keywords = ['노라', '잖습니까', '잖아요', '잖나요', 'ㅎㅎ', '^^', '맛집', '오쭈']
            for keyword in filter_keywords:
                if keyword in response:
                    return ""
        
        # 응답 길이 검증
        if len(response) < 3 or len(response) > 200:
            return ""
        
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
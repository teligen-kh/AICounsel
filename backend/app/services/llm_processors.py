from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time
import psutil
import torch
import re

class BaseLLMProcessor(ABC):
    """LLM 프로세서 기본 클래스"""
    
    def __init__(self, model_type: str):
        self.model_type = model_type
    
    @abstractmethod
    def create_casual_prompt(self, message: str) -> str:
        """일상 대화용 프롬프트 생성"""
        pass
    
    @abstractmethod
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성"""
        pass
    
    @abstractmethod
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """모델별 최적화된 생성 파라미터 반환"""
        pass
    
    @abstractmethod
    def process_response(self, response: str) -> str:
        """모델별 응답 후처리"""
        pass
    
    def log_performance_metrics(self, start_time: float, end_time: float, prompt_length: int, response_length: int):
        """성능 메트릭 로깅"""
        processing_time = (end_time - start_time) * 1000  # ms
        
        # 시스템 리소스 정보
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # GPU 정보 (사용 가능한 경우)
        gpu_info = "N/A"
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated() / 1024**3  # GB
            gpu_info = f"GPU Memory: {gpu_memory:.2f}GB"
        
        logging.info(f"=== 성능 메트릭 ===")
        logging.info(f"모델: {self.model_type}")
        logging.info(f"처리 시간: {processing_time:.2f}ms")
        logging.info(f"프롬프트 길이: {prompt_length} 토큰")
        logging.info(f"응답 길이: {response_length} 토큰")
        logging.info(f"토큰당 처리 시간: {processing_time/max(response_length, 1):.2f}ms/token")
        logging.info(f"CPU 사용률: {cpu_percent:.1f}%")
        logging.info(f"메모리 사용률: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)")
        logging.info(f"GPU 정보: {gpu_info}")
        logging.info(f"==================")

class PolyglotKoProcessor(BaseLLMProcessor):
    """Polyglot-Ko 5.8B 모델 전용 프로세서 (텍스트 완성 방식)"""
    
    def __init__(self):
        super().__init__("polyglot-ko-5.8b")
        logging.info("Polyglot-Ko 프로세서 초기화 (텍스트 완성 방식)")
    
    def create_casual_prompt(self, message: str) -> str:
        """일상 대화용 프롬프트 생성 (텍스트 완성 방식)"""
        # 텍스트 완성 모델에 맞는 프롬프트
        if message.endswith("?"):
            # 질문인 경우
            return f"{message} "
        else:
            # 일반 문장인 경우
            return f"{message} "
    
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성 (텍스트 완성 방식)"""
        return f"질문: {message}\n답변: {db_answer}\n추가 설명: "
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """Polyglot-Ko 텍스트 완성용 파라미터 (보수적)"""
        return {
            "max_new_tokens": 20,        # 적당히 짧게
            "temperature": 0.1,          # 낮게 (일관성)
            "top_p": 0.9,               # 높게 (안정성)
            "do_sample": True,           # 샘플링 활성화
            "repetition_penalty": 1.0,   # 기본값
            "num_beams": 1,             # 단일 빔
            "use_cache": True,          # 캐시 사용
            "pad_token_id": None,       # 자동 설정
            "eos_token_id": None        # 자동 설정
        }
    
    def process_response(self, response: str) -> str:
        """Polyglot-Ko 응답 후처리 (텍스트 완성 방식) - 완화된 필터링"""
        # 기본 정리
        response = response.strip()
        
        # 응답이 비어있으면 바로 반환
        if not response:
            return ""
        
        # 1. 매우 명확한 노이즈 패턴만 필터링 (완화)
        critical_noise_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URL
            r'www\.[^\s]+',  # www로 시작하는 URL
            r'^\s*[^\w가-힣\s]+\s*$',  # 특수문자만 (완화)
        ]
        
        for pattern in critical_noise_patterns:
            if re.search(pattern, response):
                logging.warning(f"중요 노이즈 패턴 발견: {pattern}")
                return ""
        
        # 2. 응답 길이 검증 (완화)
        if len(response) < 1 or len(response) > 100:  # 더 길게 허용
            return ""
        
        # 3. 매우 명확한 노이즈 키워드만 필터링 (완화)
        critical_noise_keywords = [
            'Neoalpha', 'rqproduct', '토론', 'KST'
        ]
        
        for keyword in critical_noise_keywords:
            if keyword in response:
                logging.warning(f"중요 노이즈 키워드 발견: {keyword}")
                return ""
        
        # 4. 기본적인 응답 품질 확인 (완화)
        if response in ["", " ", "\n", "\t"]:
            return ""
        
        # 5. 문장 완성 형태로 정리 (선택적)
        # 마지막 문장 부호가 없고 응답이 짧으면 추가
        if response and len(response) < 10 and not response[-1] in ['.', '!', '?', '~', '^']:
            response += '.'
        
        logging.info(f"✅ 후처리 완료 - 최종 응답: '{response}'")
        return response

class LlamaProcessor(BaseLLMProcessor):
    """LLaMA 3.1 8B Instruct 모델 전용 프로세서"""
    
    def __init__(self):
        super().__init__("llama-3.1-8b")
        logging.info("LLaMA 3.1 프로세서 초기화")
    
    def create_casual_prompt(self, message: str) -> str:
        """일상 대화용 프롬프트 생성 (LLaMA 형식)"""
        return f"""<|im_start|>user
{message}<|im_end|>
<|im_start|>assistant
"""
    
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성 (LLaMA 형식)"""
        return f"""<|im_start|>user
사용자 질문: {message}

DB 답변: {db_answer}

위 답변을 친절하고 이해하기 쉽게 정리해주세요.<|im_end|>
<|im_start|>assistant
"""
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """LLaMA 3.1 최적화 파라미터 (기본 상태로 복원)"""
        return {
            "max_new_tokens": 30,         # 기본값으로 복원
            "temperature": 0.6,           # 기본값으로 복원
            "top_p": 0.8,                # 기본값으로 복원
            "do_sample": True,            # 기본값으로 복원
            "repetition_penalty": 1.1,   # 기본값으로 복원
            "num_beams": 1,              # 기본값으로 복원
            "use_cache": True            # 캐시 유지
        }
    
    def process_response(self, response: str) -> str:
        """LLaMA 3.1 응답 후처리"""
        # LLaMA 특화 후처리
        response = response.strip()
        
        # LLaMA 특수 토큰 제거
        response = response.replace("<|im_end|>", "").replace("<|im_start|>", "")
        response = response.replace("<|endoftext|>", "")
        
        # 영어 응답을 한국어로 변환하는 로직 (필요시)
        # 현재는 기본 후처리만
        
        return response

class LLMProcessorFactory:
    """LLM 프로세서 팩토리"""
    
    @staticmethod
    def create_processor(model_type: str) -> BaseLLMProcessor:
        """모델 타입에 따른 프로세서 생성"""
        if model_type == "polyglot-ko-5.8b":
            return PolyglotKoProcessor()
        elif model_type == "llama-3.1-8b":
            return LlamaProcessor()
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {model_type}") 
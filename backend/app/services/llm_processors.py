from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

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

class PolyglotKoProcessor(BaseLLMProcessor):
    """Polyglot-Ko 5.8B 모델 전용 프로세서"""
    
    def __init__(self):
        super().__init__("polyglot-ko-5.8b")
        logging.info("Polyglot-Ko 프로세서 초기화")
    
    def create_casual_prompt(self, message: str) -> str:
        """일상 대화용 프롬프트 생성 (한국어 특화)"""
        return f"""사용자: {message}

친절하고 자연스럽게 응답해주세요:"""
    
    def create_professional_prompt(self, message: str, db_answer: str) -> str:
        """전문 상담용 프롬프트 생성 (한국어 특화)"""
        return f"""사용자 질문: {message}

DB 답변: {db_answer}

위 답변을 친절하고 이해하기 쉽게 정리해주세요:"""
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """Polyglot-Ko 최적화 파라미터"""
        return {
            "max_new_tokens": 50,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "repetition_penalty": 1.1,
            "num_beams": 1,
            "use_cache": True
        }
    
    def process_response(self, response: str) -> str:
        """Polyglot-Ko 응답 후처리"""
        # 한국어 특화 후처리
        response = response.strip()
        
        # 불필요한 접두사 제거
        prefixes_to_remove = ["답변:", "응답:", "안녕하세요!", "안녕하세요."]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
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
        """LLaMA 3.1 최적화 파라미터"""
        return {
            "max_new_tokens": 30,
            "temperature": 0.6,
            "top_p": 0.8,
            "do_sample": True,
            "repetition_penalty": 1.1,
            "num_beams": 1,
            "use_cache": True
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
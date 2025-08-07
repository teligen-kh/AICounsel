"""
AICounsel 설정 관리 모듈
애플리케이션 전체 설정과 모듈 제어 기능 제공
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경 변수와 기본값을 통한 설정 관리
    """
    # 기본 애플리케이션 설정
    app_name: str = "AICounsel"
    debug: bool = True
    
    # MongoDB 데이터베이스 연결 설정
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "aicounsel"
    db_name: str = "aicounsel"  # 호환성을 위한 별칭
    
    # LLM 모델 설정
    default_model: str = "llama-3.1-8b-instruct"
    model_path: str = "models/Llama-3.1-8B-Instruct"
    model_name: str = "llama-3.1-8b-instruct"  # 호환성을 위한 별칭
    
    # OpenAI API 설정 (선택적)
    openai_api_key: Optional[str] = None
    
    # ===== 모듈 연결/해제 설정 (코드 한 두 줄로 제어) =====
    # MongoDB 검색 모듈 활성화 여부 - DB에서 답변 검색
    ENABLE_MONGODB_SEARCH: bool = True
    
    # LLM 모델 연동 모듈 활성화 여부 - AI 모델 응답 생성
    ENABLE_LLM_MODEL: bool = True
    
    # 고객 질문 분석 모듈 활성화 여부 - 대화 유형 분류
    ENABLE_CONVERSATION_ANALYSIS: bool = True
    
    # 응답 포맷팅 모듈 활성화 여부 - 응답 텍스트 정리
    ENABLE_RESPONSE_FORMATTING: bool = True
    
    # 입력 필터링 모듈 활성화 여부 - 욕설/비상담 필터링
    ENABLE_INPUT_FILTERING: bool = True
    
    # 강화된 입력 분류 모듈 활성화 여부 - 키워드+LLM 의도 분석
    ENABLE_ENHANCED_CLASSIFICATION: bool = False
    
    # 하이브리드 응답 생성 모듈 활성화 여부 - DB+LLM 조합 응답
    ENABLE_HYBRID_RESPONSE: bool = False
    
    # 문맥 인식 분류 모듈 활성화 여부 - 키워드+LLM 하이브리드 분류
    ENABLE_CONTEXT_AWARE_CLASSIFICATION: bool = True
    
    # Clarification 모듈 활성화 여부 - 모호한 질문에 대한 추가 질문 생성
    ENABLE_CLARIFICATION: bool = True
    
    # DB 우선 모드 (True: DB 검색 우선, False: LLM 우선)
    DB_PRIORITY_MODE: bool = False
    
    # LLM 모델 타입 설정
    USE_LLAMA_CPP: bool = False      # llama-cpp-python 사용 여부
    USE_FINETUNED: bool = False      # 파인튜닝된 모델 사용 여부
    USE_TRANSFORMERS: bool = True    # transformers 라이브러리 사용 여부
    
    # 로깅 설정
    log_level: str = "INFO"          # 로그 레벨 설정
    
    class Config:
        env_file = ".env"

# 전역 설정 인스턴스 생성
settings = Settings()

# ===== 모듈 활성화/비활성화 함수 =====
def enable_module(module_name: str):
    """
    특정 모듈을 활성화합니다.
    
    Args:
        module_name: 활성화할 모듈명
    """
    if module_name == "mongodb_search":
        settings.ENABLE_MONGODB_SEARCH = True
    elif module_name == "llm_model":
        settings.ENABLE_LLM_MODEL = True
    elif module_name == "conversation_analysis":
        settings.ENABLE_CONVERSATION_ANALYSIS = True
    elif module_name == "response_formatting":
        settings.ENABLE_RESPONSE_FORMATTING = True
    elif module_name == "input_filtering":
        settings.ENABLE_INPUT_FILTERING = True
    elif module_name == "enhanced_classification":
        settings.ENABLE_ENHANCED_CLASSIFICATION = True
    elif module_name == "hybrid_response":
        settings.ENABLE_HYBRID_RESPONSE = True
    elif module_name == "context_aware_classification":
        settings.ENABLE_CONTEXT_AWARE_CLASSIFICATION = True
    elif module_name == "clarification":
        settings.ENABLE_CLARIFICATION = True
    elif module_name == "db_priority":
        settings.DB_PRIORITY_MODE = True
    else:
        raise ValueError(f"알 수 없는 모듈: {module_name}")

def disable_module(module_name: str):
    """
    특정 모듈을 비활성화합니다.
    
    Args:
        module_name: 비활성화할 모듈명
    """
    if module_name == "mongodb_search":
        settings.ENABLE_MONGODB_SEARCH = False
    elif module_name == "llm_model":
        settings.ENABLE_LLM_MODEL = False
    elif module_name == "conversation_analysis":
        settings.ENABLE_CONVERSATION_ANALYSIS = False
    elif module_name == "response_formatting":
        settings.ENABLE_RESPONSE_FORMATTING = False
    elif module_name == "input_filtering":
        settings.ENABLE_INPUT_FILTERING = False
    elif module_name == "enhanced_classification":
        settings.ENABLE_ENHANCED_CLASSIFICATION = False
    elif module_name == "hybrid_response":
        settings.ENABLE_HYBRID_RESPONSE = False
    elif module_name == "context_aware_classification":
        settings.ENABLE_CONTEXT_AWARE_CLASSIFICATION = False
    elif module_name == "clarification":
        settings.ENABLE_CLARIFICATION = False
    elif module_name == "db_priority":
        settings.DB_PRIORITY_MODE = False
    else:
        raise ValueError(f"알 수 없는 모듈: {module_name}")

def get_module_status() -> dict:
    """
    모든 모듈의 활성화 상태를 반환합니다.
    
    Returns:
        dict: 모듈명과 활성화 상태를 담은 딕셔너리
    """
    return {
        "mongodb_search": settings.ENABLE_MONGODB_SEARCH,
        "llm_model": settings.ENABLE_LLM_MODEL,
        "conversation_analysis": settings.ENABLE_CONVERSATION_ANALYSIS,
        "response_formatting": settings.ENABLE_RESPONSE_FORMATTING,
        "input_filtering": settings.ENABLE_INPUT_FILTERING,
        "enhanced_classification": settings.ENABLE_ENHANCED_CLASSIFICATION,
        "hybrid_response": settings.ENABLE_HYBRID_RESPONSE,
        "context_aware_classification": settings.ENABLE_CONTEXT_AWARE_CLASSIFICATION,
        "clarification": settings.ENABLE_CLARIFICATION,
        "db_priority_mode": settings.DB_PRIORITY_MODE
    }

def print_module_status():
    """
    모듈 상태를 콘솔에 출력합니다.
    각 모듈의 활성화/비활성화 상태를 시각적으로 표시
    """
    status = get_module_status()
    print("\n=== 모듈 활성화 상태 ===")
    for module, enabled in status.items():
        status_str = "✅ 활성화" if enabled else "❌ 비활성화"
        print(f"{module}: {status_str}")
    print("=======================\n") 
from motor.motor_asyncio import AsyncIOMotorDatabase
from .database import get_database
from .services.llm_service import LLMService
from .services.model_manager import get_model_manager
import logging

# 전역 서비스 인스턴스들
_llm_service = None
_chat_service = None

def get_llm_service() -> LLMService:
    """전역 LLM 서비스 인스턴스를 반환합니다."""
    global _llm_service
    if _llm_service is None:
        # main.py에서 초기화된 인스턴스를 가져오려고 시도
        try:
            from .main import get_llm_service as get_main_llm_service
            _llm_service = get_main_llm_service()
            if _llm_service is None:
                # main에서 초기화되지 않은 경우 새로 생성
                logging.warning("Creating new LLM service instance")
                db = get_database()
                model_manager = get_model_manager()
                current_model = model_manager.current_model or "polyglot-ko-5.8b"
                _llm_service = LLMService(db=db, use_db_priority=True, model_type=current_model)
        except ImportError:
            # main 모듈을 import할 수 없는 경우 새로 생성
            logging.warning("Cannot import main module, creating new LLM service instance")
            db = get_database()
            model_manager = get_model_manager()
            current_model = model_manager.current_model or "polyglot-ko-5.8b"
            _llm_service = LLMService(db=db, use_db_priority=True, model_type=current_model)
    return _llm_service

def get_chat_service():
    """전역 ChatService 인스턴스를 반환합니다."""
    global _chat_service
    if _chat_service is None:
        # Lazy import to avoid circular dependency
        from .services.chat_service import ChatService
        db = get_database()
        llm_service = get_llm_service()
        _chat_service = ChatService(db=db, llm_service=llm_service)
    return _chat_service

def set_llm_service(service: LLMService):
    """전역 LLM 서비스 인스턴스를 설정합니다."""
    global _llm_service
    _llm_service = service

def set_chat_service(service):
    """전역 ChatService 인스턴스를 설정합니다."""
    global _chat_service
    _chat_service = service 
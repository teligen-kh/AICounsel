from motor.motor_asyncio import AsyncIOMotorDatabase
from .database import get_database
from .services.llm_service import LLMService
from .services.chat_service import ChatService
from .services.mongodb_search_service import MongoDBSearchService
from .services.conversation_algorithm import ConversationAlgorithm
from .services.formatting_service import FormattingService
from .services.model_manager import get_model_manager, ModelType
import logging
from typing import Optional
import os

# 전역 서비스 인스턴스
_llm_service: Optional[LLMService] = None
_chat_service: Optional[ChatService] = None
_search_service: Optional[MongoDBSearchService] = None
_conversation_algorithm: Optional[ConversationAlgorithm] = None
_formatting_service: Optional[FormattingService] = None

def _should_use_llama_cpp() -> bool:
    """llama-cpp 사용 여부를 결정합니다."""
    # Llama-3.1-8B-Instruct 모델을 사용하므로 transformers 사용
    return False

async def get_llm_service() -> LLMService:
    """LLM 서비스 인스턴스를 반환합니다."""
    global _llm_service
    if _llm_service is None:
        # 순수 LLM 모드로 초기화 (DB 비활성화)
        logging.info("순수 LLM 모드로 LLM 서비스를 초기화합니다.")
        _llm_service = LLMService(use_db_mode=False, use_llama_cpp=False, use_finetuned=False)
        
        logging.info("LLM 서비스 인스턴스 생성 완료")
    return _llm_service

async def get_chat_service() -> ChatService:
    """채팅 서비스 인스턴스를 반환합니다."""
    global _chat_service
    if _chat_service is None:
        db = await get_database()
        llm_service = await get_llm_service()
        _chat_service = ChatService(db, llm_service)
        logging.info("채팅 서비스 인스턴스 생성 완료")
    return _chat_service

async def get_search_service() -> MongoDBSearchService:
    """MongoDB 검색 서비스 인스턴스를 반환합니다."""
    global _search_service
    if _search_service is None:
        db = await get_database()
        _search_service = MongoDBSearchService(db)
        logging.info("MongoDB 검색 서비스 인스턴스 생성 완료")
    return _search_service

def get_conversation_algorithm() -> ConversationAlgorithm:
    """고객 응대 알고리즘 인스턴스를 반환합니다."""
    global _conversation_algorithm
    if _conversation_algorithm is None:
        _conversation_algorithm = ConversationAlgorithm()
        logging.info("고객 응대 알고리즘 인스턴스 생성 완료")
    return _conversation_algorithm

def get_formatting_service() -> FormattingService:
    """포맷팅 서비스 인스턴스를 반환합니다."""
    global _formatting_service
    if _formatting_service is None:
        _formatting_service = FormattingService()
        logging.info("포맷팅 서비스 인스턴스 생성 완료")
    return _formatting_service

def reset_services():
    """모든 서비스 인스턴스를 초기화합니다."""
    global _llm_service, _chat_service, _search_service, _conversation_algorithm, _formatting_service
    _llm_service = None
    _chat_service = None
    _search_service = None
    _conversation_algorithm = None
    _formatting_service = None
    logging.info("모든 서비스 인스턴스 초기화 완료")

def get_model_manager():
    """모델 매니저 인스턴스를 반환합니다."""
    return get_model_manager()

def enable_db_mode():
    """DB 연동 모드를 활성화합니다."""
    global _llm_service
    if _llm_service:
        db = get_database()
        search_service = MongoDBSearchService(db)
        _llm_service.inject_db_service(search_service)
        _llm_service.set_db_mode(True)
        logging.info("DB 연동 모드 활성화 완료")

def disable_db_mode():
    """DB 연동 모드를 비활성화합니다."""
    global _llm_service
    if _llm_service:
        _llm_service.remove_db_service()
        _llm_service.set_db_mode(False)
        logging.info("DB 연동 모드 비활성화 완료")

# FastAPI 의존성 함수들
async def get_db() -> AsyncIOMotorDatabase:
    """데이터베이스 연결을 반환합니다."""
    return await get_database()

async def get_llm_service_dependency() -> LLMService:
    """LLM 서비스 의존성을 반환합니다."""
    return await get_llm_service()

async def get_chat_service_dependency() -> ChatService:
    """채팅 서비스 의존성을 반환합니다."""
    return await get_chat_service()

async def get_search_service_dependency() -> MongoDBSearchService:
    """검색 서비스 의존성을 반환합니다."""
    return await get_search_service()

async def get_conversation_algorithm_dependency() -> ConversationAlgorithm:
    """고객 응대 알고리즘 의존성을 반환합니다."""
    return get_conversation_algorithm()

async def get_formatting_service_dependency() -> FormattingService:
    """포맷팅 서비스 의존성을 반환합니다."""
    return get_formatting_service() 
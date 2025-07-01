from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from ...models.chat import ChatMessage, ChatResponse
from ...services.chat_service import ChatService
from ...services.llm_service import LLMService
from ...services.model_manager import get_model_manager, ModelType
from ...database import get_database
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()

def get_llm_service(db) -> LLMService:
    """전역 LLM 서비스 인스턴스를 반환합니다."""
    try:
        # main.py의 전역 인스턴스 사용
        from ...main import get_llm_service as get_global_llm_service
        global_service = get_global_llm_service()
        if global_service and global_service.model and global_service.tokenizer:
            logging.info("Using global LLM service instance")
            return global_service
        else:
            logging.warning("Global LLM service not ready, creating new instance")
            return LLMService(db=db, use_db_priority=True)
    except ImportError:
        # main 모듈을 import할 수 없는 경우
        logging.warning("Cannot import main module, creating new LLM service instance")
        return LLMService(db=db, use_db_priority=True)

class StatsResponse(BaseModel):
    total_requests: int
    db_responses: int
    algorithm_responses: int
    errors: int
    avg_processing_time: float
    avg_db_processing_time: float
    avg_algorithm_processing_time: float
    median_processing_time: float
    min_processing_time: float
    max_processing_time: float

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

class ModelSwitchRequest(BaseModel):
    model_type: str

class ModelStatusResponse(BaseModel):
    current_model: str
    available_models: List[str]
    loaded_models: List[str]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db=Depends(get_database)):
    """채팅 API"""
    try:
        logging.info(f"Received chat request: {request.message}")
        chat_service = ChatService(db)
        logging.info("ChatService initialized")
        response = await chat_service.process_message(request.message, request.conversation_id)
        logging.info(f"Generated response: {response[:100]}...")
        return ChatResponse(response=response, conversation_id=request.conversation_id or "new")
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/switch-model")
async def switch_model(request: ModelSwitchRequest):
    """모델 전환 API"""
    try:
        model_manager = get_model_manager()
        
        # 사용 가능한 모델인지 확인
        if request.model_type not in model_manager.get_available_models():
            raise HTTPException(status_code=400, detail=f"Unknown model type: {request.model_type}")
        
        # 모델 전환
        success = model_manager.switch_model(request.model_type)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to switch to model: {request.model_type}")
        
        return {"message": f"Successfully switched to {request.model_type}", "current_model": request.model_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Model switch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/model-status", response_model=ModelStatusResponse)
async def get_model_status():
    """모델 상태 확인 API"""
    try:
        model_manager = get_model_manager()
        
        return ModelStatusResponse(
            current_model=model_manager.current_model or "none",
            available_models=model_manager.get_available_models(),
            loaded_models=model_manager.get_loaded_models()
        )
        
    except Exception as e:
        logging.error(f"Model status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    before: Optional[datetime] = None,
    db = Depends(get_database)
):
    try:
        chat_service = ChatService(db)
        messages = await chat_service.get_chat_history(session_id, limit, before)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/db-mode")
async def set_db_priority_mode(
    enabled: bool,
    db = Depends(get_database)
):
    """DB 우선 검색 모드를 설정합니다."""
    try:
        llm_service = get_llm_service(db)
        llm_service.set_db_priority_mode(enabled)
        return {"message": f"DB priority mode {'enabled' if enabled else 'disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/db-mode")
async def get_db_priority_mode(db = Depends(get_database)):
    """현재 DB 우선 검색 모드 상태를 반환합니다."""
    try:
        llm_service = get_llm_service(db)
        return {"db_priority_mode": llm_service.use_db_priority}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StatsResponse)
async def get_response_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """응답 시간 통계를 반환합니다."""
    try:
        llm_service = get_llm_service(db)
        stats = llm_service.get_response_stats()
        
        return StatsResponse(
            total_requests=stats['total_requests'],
            db_responses=stats['db_responses'],
            algorithm_responses=stats['algorithm_responses'],
            errors=stats['errors'],
            avg_processing_time=stats['avg_processing_time'],
            avg_db_processing_time=stats['avg_db_processing_time'],
            avg_algorithm_processing_time=stats['avg_algorithm_processing_time'],
            median_processing_time=stats['median_processing_time'],
            min_processing_time=stats['min_processing_time'],
            max_processing_time=stats['max_processing_time']
        )
    except Exception as e:
        logging.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="통계 조회 중 오류가 발생했습니다.")

@router.post("/stats/log")
async def log_response_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """응답 시간 통계를 로그로 출력합니다."""
    try:
        llm_service = get_llm_service(db)
        llm_service.log_response_stats()
        return {"message": "통계가 로그에 출력되었습니다."}
    except Exception as e:
        logging.error(f"Stats log error: {str(e)}")
        raise HTTPException(status_code=500, detail="통계 로그 출력 중 오류가 발생했습니다.") 
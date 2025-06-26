from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from ...models.chat import ChatMessage, ChatResponse
from ...services.chat_service import ChatService
from ...services.llm_service import LLMService
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

@router.post("/chat", response_model=ChatResponse)
async def process_chat(
    message: ChatMessage,
    use_db_priority: bool = Query(True, description="DB 우선 검색 모드 사용 여부"),
    db = Depends(get_database)
):
    try:
        import logging
        logging.info(f"Received chat message: {message.content[:50]}...")
        
        # LLM 서비스 가져오기
        llm_service = get_llm_service(db)
        logging.info("LLM service initialized")
        
        # DB 우선 검색 모드 설정
        llm_service.set_db_priority_mode(use_db_priority)
        logging.info(f"DB priority mode set to: {use_db_priority}")
        
        # 채팅 서비스 초기화
        chat_service = ChatService(db)
        logging.info("Chat service initialized")
        
        # 메시지 저장
        await chat_service.save_message(message)
        logging.info("Message saved to database")
        
        # LLM 응답 생성
        response_text = await llm_service.process_message(message.content, message.session_id)
        logging.info(f"Generated response: {response_text[:50]}...")
        logging.info(f"Full response with newlines: {repr(response_text)}")
        
        # 응답 메시지 생성
        assistant_message = ChatMessage(
            content=response_text,
            role="assistant",
            session_id=message.session_id,
            timestamp=datetime.now()
        )
        
        # 응답 메시지 저장
        await chat_service.save_message(assistant_message)
        logging.info("Assistant message saved to database")
        
        return ChatResponse(
            response=response_text,
            context={
                "model": "llama2-chat",
                "db_priority_mode": use_db_priority
            }
        )
    except Exception as e:
        import logging
        logging.error(f"Error in process_chat: {str(e)}")
        logging.error(f"Error type: {type(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
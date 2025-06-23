from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from ...models.chat import ChatMessage, ChatResponse
from ...services.chat_service import ChatService
from ...services.llm_service import LLMService
from ...database import get_database

router = APIRouter()

# 전역 LLM 서비스 인스턴스 (DB 연결 후 초기화)
llm_service = None

def get_llm_service(db) -> LLMService:
    """LLM 서비스 인스턴스를 반환합니다."""
    global llm_service
    if llm_service is None:
        llm_service = LLMService(db=db, use_db_priority=True)
    return llm_service

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
        response_text = await llm_service.get_response(message.session_id, message.content)
        logging.info(f"Generated response: {response_text[:50]}...")
        
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
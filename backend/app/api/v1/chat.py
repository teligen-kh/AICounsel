from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from ...models.chat import ChatMessage, ChatResponse
from ...services.chat_service import ChatService
from ...services.llm_service import LLMService
from ...database import get_database

router = APIRouter()
llm_service = LLMService()

@router.post("/chat", response_model=ChatResponse)
async def process_chat(
    message: ChatMessage,
    db = Depends(get_database)
):
    try:
        # 채팅 서비스 초기화
        chat_service = ChatService(db)
        
        # 메시지 저장
        await chat_service.save_message(message)
        
        # LLM 응답 생성
        response_text = await llm_service.get_response(message.session_id, message.content)
        
        # 응답 메시지 생성
        assistant_message = ChatMessage(
            content=response_text,
            role="assistant",
            session_id=message.session_id,
            timestamp=datetime.now()
        )
        
        # 응답 메시지 저장
        await chat_service.save_message(assistant_message)
        
        return ChatResponse(
            response=response_text,
            context={"model": "llama2-chat"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
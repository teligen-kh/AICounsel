from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from ..database import get_database
from datetime import datetime

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@router.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    try:
        db = await get_database()
        collection = db.conversations
        
        # 대화 내용 저장
        conversation = {
            'messages': [msg.dict() for msg in request.messages],
            'created_at': datetime.utcnow()
        }
        
        result = await collection.insert_one(conversation)
        
        return {
            'status': 'success',
            'conversation_id': str(result.inserted_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
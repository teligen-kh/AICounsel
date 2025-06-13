from fastapi import APIRouter, HTTPException
from ..models.chat import ChatRequest, ChatResponse
from ..services.chat import process_message

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response_content = await process_message(request.message)
        return ChatResponse(content=response_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        ) 
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..dependencies import get_db, get_chat_service_dependency, get_llm_service_dependency
from ..services.chat_service import ChatService
from ..services.llm_service import LLMService
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    processing_time: Optional[float] = None

class ModelSwitchRequest(BaseModel):
    model_type: str

class ModelStatusResponse(BaseModel):
    current_model: str
    model_loaded: bool
    model_settings: Optional[Dict[str, Any]] = None
    db_priority_mode: bool
    error: Optional[str] = None

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    채팅 메시지를 처리하고 응답을 반환합니다.
    
    Args:
        request: 채팅 요청 (메시지, 대화 ID)
        db: 데이터베이스 연결
        chat_service: 채팅 서비스
        
    Returns:
        채팅 응답 (응답, 대화 ID, 처리 시간)
    """
    try:
        import time
        start_time = time.time()
        
        # 메시지 처리
        response = await chat_service.process_message(
            request.message, 
            request.conversation_id
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response,
            conversation_id=request.conversation_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"채팅 메시지 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메시지 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/switch-model")
async def switch_model(
    request: ModelSwitchRequest,
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    LLM 모델을 전환합니다.
    
    Args:
        request: 모델 전환 요청
        chat_service: 채팅 서비스
        
    Returns:
        전환 결과
    """
    try:
        success = chat_service.switch_model(request.model_type)
        
        if success:
            return {
                "success": True,
                "message": f"모델이 {request.model_type}로 전환되었습니다.",
                "current_model": request.model_type
            }
        else:
            raise HTTPException(status_code=400, detail="모델 전환에 실패했습니다.")
            
    except Exception as e:
        logging.error(f"모델 전환 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 전환 중 오류가 발생했습니다: {str(e)}")

@router.get("/model-status", response_model=ModelStatusResponse)
async def get_model_status(
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    현재 모델 상태를 조회합니다.
    
    Args:
        chat_service: 채팅 서비스
        
    Returns:
        모델 상태 정보
    """
    try:
        status = chat_service.get_model_status()
        return ModelStatusResponse(**status)
        
    except Exception as e:
        logging.error(f"모델 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 상태 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/stats")
async def get_chat_stats(
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    채팅 통계를 조회합니다.
    
    Args:
        chat_service: 채팅 서비스
        
    Returns:
        채팅 통계 정보
    """
    try:
        stats = chat_service.get_response_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logging.error(f"채팅 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/set-db-priority")
async def set_db_priority_mode(
    enabled: bool = Query(..., description="DB 우선 검색 모드 활성화 여부"),
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    DB 우선 검색 모드를 설정합니다.
    
    Args:
        enabled: DB 우선 검색 모드 활성화 여부
        chat_service: 채팅 서비스
        
    Returns:
        설정 결과
    """
    try:
        chat_service.set_db_priority_mode(enabled)
        
        return {
            "success": True,
            "message": f"DB 우선 검색 모드가 {'활성화' if enabled else '비활성화'}되었습니다.",
            "db_priority_mode": enabled
        }
        
    except Exception as e:
        logging.error(f"DB 우선 검색 모드 설정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB 우선 검색 모드 설정 중 오류가 발생했습니다: {str(e)}")

@router.post("/reset-services")
async def reset_services(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    모든 서비스 인스턴스를 초기화합니다.
    
    Args:
        db: 데이터베이스 연결
        
    Returns:
        초기화 결과
    """
    try:
        from ..dependencies import reset_services
        reset_services()
        
        return {
            "success": True,
            "message": "모든 서비스 인스턴스가 초기화되었습니다."
        }
        
    except Exception as e:
        logging.error(f"서비스 초기화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서비스 초기화 중 오류가 발생했습니다: {str(e)}")

# ===== 업무별 API 엔드포인트 =====

@router.post("/casual", response_model=ChatResponse)
async def handle_casual_conversation(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    일상 대화 처리 - 대화 정보 받기
    
    Args:
        request: 채팅 요청
        chat_service: 채팅 서비스
        
    Returns:
        일상 대화 응답
    """
    try:
        import time
        start_time = time.time()
        
        response = await chat_service.get_conversation_response(request.message)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response,
            conversation_id=request.conversation_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"일상 대화 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일상 대화 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/professional", response_model=ChatResponse)
async def handle_professional_conversation(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    전문 상담 처리 - 응답 찾기
    
    Args:
        request: 채팅 요청
        chat_service: 채팅 서비스
        
    Returns:
        전문 상담 응답
    """
    try:
        import time
        start_time = time.time()
        
        response = await chat_service.search_and_enhance_answer(request.message)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response,
            conversation_id=request.conversation_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"전문 상담 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"전문 상담 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/format", response_model=ChatResponse)
async def format_response(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service_dependency)
):
    """
    응답 포맷팅 - 응답 정보 보내기
    
    Args:
        request: 채팅 요청 (message 필드에 포맷팅할 응답)
        chat_service: 채팅 서비스
        
    Returns:
        포맷팅된 응답
    """
    try:
        import time
        start_time = time.time()
        
        formatted_response = await chat_service.format_and_send_response(request.message)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=formatted_response,
            conversation_id=request.conversation_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"응답 포맷팅 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 포맷팅 중 오류가 발생했습니다: {str(e)}") 
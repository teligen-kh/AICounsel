from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...models.chat import ChatMessage, ChatResponse
from ...services.chat_service import ChatService
from ...services.llm_service import LLMService
from ...services.model_manager import get_model_manager, ModelType
from ...database import get_database
from ...dependencies import get_chat_service, get_llm_service
from ...config import enable_module, disable_module, get_module_status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()

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

class PerformanceMetricsResponse(BaseModel):
    model_performance: Dict[str, Any]
    system_metrics: Dict[str, Any]
    llm_stats: Dict[str, Any]

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

class ModuleControlRequest(BaseModel):
    module_name: str
    action: str  # "enable" or "disable"

class ModuleStatusResponse(BaseModel):
    modules: Dict[str, bool]
    message: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """채팅 API"""
    import time
    start_time = time.time()
    
    try:
        logging.info(f"=== API 요청 시작 ===")
        logging.info(f"요청 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"입력 메시지: '{request.message}'")
        logging.info(f"대화 ID: {request.conversation_id}")
        logging.info(f"메시지 길이: {len(request.message)}")
        
        # ChatService 초기화 확인
        logging.info("ChatService 의존성 주입 확인...")
        if chat_service is None:
            logging.error("❌ ChatService가 None입니다!")
            raise HTTPException(status_code=500, detail="ChatService 초기화 실패")
        logging.info("✅ ChatService 의존성 주입 완료")
        
        # 메시지 처리 시작
        logging.info("메시지 처리 시작...")
        process_start = time.time()
        response = await chat_service.process_message(request.message, request.conversation_id)
        process_time = (time.time() - process_start) * 1000
        logging.info(f"✅ 메시지 처리 완료 - 시간: {process_time:.2f}ms")
        
        # 응답 검증
        logging.info(f"응답 길이: {len(response) if response else 0}")
        logging.info(f"응답 내용: '{response[:200] if response else 'None'}...'")
        
        if not response or len(response.strip()) == 0:
            logging.warning("⚠️ 응답이 비어있습니다!")
            response = "죄송합니다. 응답을 생성하는 중에 문제가 발생했습니다."
        
        # 전체 처리 시간 계산
        total_time = (time.time() - start_time) * 1000
        logging.info(f"=== API 요청 완료 ===")
        logging.info(f"전체 처리 시간: {total_time:.2f}ms")
        logging.info(f"메시지 처리 시간: {process_time:.2f}ms")
        logging.info(f"API 오버헤드: {total_time - process_time:.2f}ms")
        
        return ChatResponse(response=response, conversation_id=request.conversation_id or "new")
        
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        logging.error(f"=== API 오류 발생 ===")
        logging.error(f"오류 발생 시간: {error_time:.2f}ms")
        logging.error(f"오류 내용: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")
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
    chat_service: ChatService = Depends(get_chat_service)
):
    try:
        messages = await chat_service.get_chat_history(session_id, limit, before)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/db-mode")
async def set_db_priority_mode(
    enabled: bool,
    llm_service: LLMService = Depends(get_llm_service)
):
    """DB 우선 검색 모드를 설정합니다."""
    try:
        llm_service.set_db_priority_mode(enabled)
        return {"message": f"DB priority mode {'enabled' if enabled else 'disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/db-mode")
async def get_db_priority_mode(llm_service: LLMService = Depends(get_llm_service)):
    """현재 DB 우선 검색 모드 상태를 반환합니다."""
    try:
        return {"db_priority_mode": llm_service.use_db_priority}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StatsResponse)
async def get_response_stats(llm_service: LLMService = Depends(get_llm_service)):
    """응답 시간 통계를 반환합니다."""
    try:
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
async def log_response_stats(llm_service: LLMService = Depends(get_llm_service)):
    """응답 시간 통계를 로그로 출력합니다."""
    try:
        llm_service.log_response_stats()
        return {"message": "통계가 로그에 출력되었습니다."}
    except Exception as e:
        logging.error(f"Stats log error: {str(e)}")
        raise HTTPException(status_code=500, detail="통계 로그 출력 중 오류가 발생했습니다.")

# ===== 성능 모니터링 API =====

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    llm_service: LLMService = Depends(get_llm_service)
):
    """종합 성능 메트릭을 반환합니다."""
    try:
        import psutil
        import torch
        
        # 모델 매니저 성능 통계
        model_manager = get_model_manager()
        model_stats = model_manager.get_performance_stats()
        
        # 시스템 메트릭
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        gpu_info = "N/A"
        if torch.cuda.is_available():
            gpu_memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            gpu_memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            gpu_info = {
                "allocated_gb": round(gpu_memory_allocated, 2),
                "reserved_gb": round(gpu_memory_reserved, 2),
                "available": True
            }
        else:
            gpu_info = {"available": False}
        
        system_metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / 1024**3, 2),
            "memory_total_gb": round(memory.total / 1024**3, 2),
            "gpu": gpu_info
        }
        
        # LLM 서비스 통계
        llm_stats = llm_service.get_response_stats()
        
        return PerformanceMetricsResponse(
            model_performance=model_stats,
            system_metrics=system_metrics,
            llm_stats=llm_stats
        )
        
    except Exception as e:
        logging.error(f"Performance metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="성능 메트릭 조회 중 오류가 발생했습니다.")

@router.post("/performance/log")
async def log_performance_summary():
    """성능 요약을 로그로 출력합니다."""
    try:
        model_manager = get_model_manager()
        model_manager.log_performance_summary()
        
        llm_service = get_llm_service()
        llm_service.log_response_stats()
        
        return {"message": "성능 요약이 로그에 출력되었습니다."}
    except Exception as e:
        logging.error(f"Performance log error: {str(e)}")
        raise HTTPException(status_code=500, detail="성능 로그 출력 중 오류가 발생했습니다.")

@router.get("/performance/system")
async def get_system_metrics():
    """시스템 메트릭만 반환합니다."""
    try:
        import psutil
        import torch
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        gpu_info = "N/A"
        if torch.cuda.is_available():
            gpu_memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            gpu_memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            gpu_info = {
                "allocated_gb": round(gpu_memory_allocated, 2),
                "reserved_gb": round(gpu_memory_reserved, 2),
                "available": True
            }
        else:
            gpu_info = {"available": False}
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / 1024**3, 2),
            "memory_total_gb": round(memory.total / 1024**3, 2),
            "gpu": gpu_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"System metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="시스템 메트릭 조회 중 오류가 발생했습니다.")

# ===== 모듈 제어 API =====

@router.post("/modules/control", response_model=ModuleStatusResponse)
async def control_module(request: ModuleControlRequest):
    """모듈을 활성화하거나 비활성화합니다."""
    try:
        if request.action == "enable":
            enable_module(request.module_name)
            message = f"✅ {request.module_name} 모듈이 활성화되었습니다."
        elif request.action == "disable":
            disable_module(request.module_name)
            message = f"❌ {request.module_name} 모듈이 비활성화되었습니다."
        else:
            raise HTTPException(status_code=400, detail="잘못된 액션입니다. 'enable' 또는 'disable'을 사용하세요.")
        
        modules = get_module_status()
        return ModuleStatusResponse(modules=modules, message=message)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"모듈 제어 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모듈 제어 실패: {str(e)}")

@router.get("/modules/status", response_model=ModuleStatusResponse)
async def get_modules_status():
    """모든 모듈의 상태를 반환합니다."""
    try:
        modules = get_module_status()
        message = "모듈 상태 조회 완료"
        return ModuleStatusResponse(modules=modules, message=message)
        
    except Exception as e:
        logging.error(f"모듈 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모듈 상태 조회 실패: {str(e)}")

@router.post("/modules/reset")
async def reset_modules():
    """모든 모듈을 기본 상태로 초기화합니다."""
    try:
        # 모든 모듈 활성화
        enable_module("mongodb_search")
        enable_module("llm_model")
        enable_module("conversation_analysis")
        enable_module("response_formatting")
        enable_module("input_filtering")
        
        modules = get_module_status()
        message = "✅ 모든 모듈이 기본 상태로 초기화되었습니다."
        return ModuleStatusResponse(modules=modules, message=message)
        
    except Exception as e:
        logging.error(f"모듈 초기화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모듈 초기화 실패: {str(e)}") 
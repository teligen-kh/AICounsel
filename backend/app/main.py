from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase
from .database import get_database, connect_to_mongo, close_mongo_connection
from .dependencies import get_chat_service_dependency, get_llm_service_dependency
from .services.chat_service import ChatService
from .services.llm_service import LLMService
from .routers import chat
from .api.v1 import auth
from .services.model_manager import get_model_manager, ModelType
import logging
import uvicorn
from contextlib import asynccontextmanager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    logger.info("애플리케이션 시작 중...")
    
    try:
        # 데이터베이스 연결 초기화
        await connect_to_mongo()
        logger.info("데이터베이스 연결 완료")
        
        # LLM 서비스 초기화 (llama-cpp-python 사용)
        from .dependencies import get_llm_service
        llm_service = await get_llm_service()
        logger.info("LLM 서비스 초기화 완료")
        
        # 채팅 서비스 초기화
        from .dependencies import get_chat_service
        chat_service = await get_chat_service()
        
        # LLM 서비스를 ContextAwareClassifier에 주입
        await chat_service.inject_llm_service()
        
        logger.info("채팅 서비스 초기화 완료")
        
        # 서비스 초기화 완료
        logger.info("모든 서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"애플리케이션 초기화 오류: {str(e)}")
    
    yield
    
    # 종료 시 정리
    logger.info("애플리케이션 종료 중...")
    try:
        # 서비스 정리
        from .dependencies import reset_services
        reset_services()
        
        # 데이터베이스 연결 종료
        await close_mongo_connection()
        logger.info("서비스 정리 완료")
    except Exception as e:
        logger.error(f"애플리케이션 정리 오류: {str(e)}")

# FastAPI 앱 생성
app = FastAPI(
    title="AI Counsel API",
    description="AI 상담 서비스 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

# 키워드 관리 API 추가
from .api.v1 import keywords
app.include_router(keywords.router, prefix="/api/v1")
# 문맥 관리 API 추가
from .api.v1 import context
app.include_router(context.router, prefix="/api/v1")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "AI Counsel API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 데이터베이스 연결 확인
        db = get_database()
        await db.command("ping")
        
        # 모델 상태 확인
        model_manager = get_model_manager()
        current_model = model_manager.get_current_model()
        
        return {
            "status": "healthy",
            "database": "connected",
            "model_loaded": current_model is not None,
            "current_model": model_manager.current_model or "unknown"
        }
    except Exception as e:
        logger.error(f"헬스 체크 오류: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/v1/info")
async def get_api_info(
    chat_service: ChatService = Depends(get_chat_service_dependency),
    llm_service: LLMService = Depends(get_llm_service_dependency)
):
    """API 정보 조회"""
    try:
        # 모델 상태
        model_status = chat_service.get_model_status()
        
        # 통계 정보
        chat_stats = chat_service.get_response_stats()
        llm_stats = llm_service.get_response_stats()
        
        return {
            "api_info": {
                "name": "AI Counsel API",
                "version": "1.0.0",
                "description": "AI 상담 서비스 API"
            },
            "model_status": model_status,
            "chat_stats": chat_stats,
            "llm_stats": llm_stats
        }
    except Exception as e:
        logger.error(f"API 정보 조회 오류: {str(e)}")
        return {
            "error": str(e)
        }

@app.post("/api/v1/llm/enable-db")
async def enable_db_mode():
    """DB 연동 모드를 활성화합니다."""
    try:
        from .dependencies import enable_db_mode
        enable_db_mode()
        return {"message": "DB 연동 모드가 활성화되었습니다.", "status": "success"}
    except Exception as e:
        logger.error(f"DB 모드 활성화 오류: {str(e)}")
        return {"message": f"DB 모드 활성화 실패: {str(e)}", "status": "error"}

@app.post("/api/v1/llm/disable-db")
async def disable_db_mode():
    """DB 연동 모드를 비활성화합니다."""
    try:
        from .dependencies import disable_db_mode
        disable_db_mode()
        return {"message": "DB 연동 모드가 비활성화되었습니다.", "status": "success"}
    except Exception as e:
        logger.error(f"DB 모드 비활성화 오류: {str(e)}")
        return {"message": f"DB 모드 비활성화 실패: {str(e)}", "status": "error"}

@app.post("/api/v1/classification/enable-context-aware")
async def enable_context_aware_classification():
    """문맥 인식 분류 모듈을 활성화합니다."""
    try:
        from .config import enable_module
        enable_module("context_aware_classification")
        return {"message": "문맥 인식 분류 모듈이 활성화되었습니다.", "status": "success"}
    except Exception as e:
        logger.error(f"문맥 인식 분류 모듈 활성화 오류: {str(e)}")
        return {"message": f"문맥 인식 분류 모듈 활성화 실패: {str(e)}", "status": "error"}

@app.post("/api/v1/classification/disable-context-aware")
async def disable_context_aware_classification():
    """문맥 인식 분류 모듈을 비활성화합니다."""
    try:
        from .config import disable_module
        disable_module("context_aware_classification")
        return {"message": "문맥 인식 분류 모듈이 비활성화되었습니다.", "status": "success"}
    except Exception as e:
        logger.error(f"문맥 인식 분류 모듈 비활성화 오류: {str(e)}")
        return {"message": f"문맥 인식 분류 모듈 비활성화 실패: {str(e)}", "status": "error"}

@app.get("/api/v1/llm/status")
async def get_llm_status():
    """LLM 서비스 상태를 조회합니다."""
    try:
        from .dependencies import get_llm_service
        llm_service = await get_llm_service()
        
        return {
            "db_mode": llm_service.use_db_mode,
            "db_service_available": llm_service.search_service is not None,
            "model_type": llm_service.model_type,
            "stats": llm_service.get_response_stats()
        }
    except Exception as e:
        logger.error(f"LLM 상태 조회 오류: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
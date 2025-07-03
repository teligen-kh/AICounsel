from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase
from .database import get_database
from .dependencies import get_chat_service_dependency, get_llm_service_dependency
from .services.chat_service import ChatService
from .services.llm_service import LLMService
from .routers import chat
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
        from .database import connect_to_mongo
        await connect_to_mongo()
        logger.info("데이터베이스 연결 완료")
        
        # 모델 매니저 초기화
        model_manager = get_model_manager()
        default_model = ModelType.POLYGLOT_KO_5_8B.value
        success = model_manager.load_model(default_model)
        
        if success:
            logger.info(f"기본 모델 로드 완료: {default_model}")
        else:
            logger.warning(f"기본 모델 로드 실패: {default_model}")
        
        # 서비스 초기화 (의존성 주입을 통해 자동으로 생성됨)
        logger.info("서비스 초기화 완료")
        
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
        from .database import close_mongo_connection
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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
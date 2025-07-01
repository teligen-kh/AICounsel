from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router
from app.api.v1.knowledge import router as knowledge_router
from .config import settings
from .database import connect_to_mongo, close_mongo_connection, get_database
from .api import chat, analysis
from .services.llm_service import LLMService
from .services.model_manager import get_model_manager, ModelType
import logging
import os
import json
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AICounsel API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(knowledge_router, prefix="/api/v1", tags=["knowledge"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

# 전역 LLM 서비스 인스턴스
llm_service = None

# 모델 상태 파일 경로
MODEL_STATUS_FILE = "model_status.json"

def get_llm_service():
    """전역 LLM 서비스 인스턴스를 반환합니다."""
    return llm_service

def save_model_status(loaded: bool, timestamp: float):
    """모델 로딩 상태를 파일에 저장합니다."""
    try:
        status = {
            "loaded": loaded,
            "timestamp": timestamp,
            "model_path": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "models", "Llama-3.1-8B-Instruct")
        }
        with open(MODEL_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Failed to save model status: {str(e)}")

def load_model_status():
    """모델 로딩 상태를 파일에서 읽어옵니다."""
    try:
        if os.path.exists(MODEL_STATUS_FILE):
            with open(MODEL_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load model status: {str(e)}")
    return None

def is_model_ready():
    """모델이 로딩되어 사용 가능한지 확인합니다."""
    global llm_service
    return llm_service is not None and llm_service.model is not None and llm_service.tokenizer is not None

# 이벤트 핸들러
@app.on_event("startup")
async def startup_db_client():
    global llm_service
    
    # MongoDB 연결
    await connect_to_mongo()
    logging.info("Connected to MongoDB.")
    
    # 모델 매니저 초기화
    model_manager = get_model_manager()
    
    # 기본 모델 로딩 (LLaMA 3.1 8B)
    try:
        logging.info("Starting model pre-loading...")
        
        # 데이터베이스 연결 가져오기
        db = await get_database()
        if db is None:
            logging.error("Failed to get database connection")
            return
        
        # LLM 서비스 초기화 (기본 모델: LLaMA 3.1 8B)
        llm_service = LLMService(db, use_db_priority=True, model_type=ModelType.LLAMA_3_1_8B.value)
        
        # 모델 로딩 완료까지 대기 (최대 5분)
        max_wait_time = 300  # 5분
        wait_time = 0
        
        while not model_manager.is_model_loaded(ModelType.LLAMA_3_1_8B.value) and wait_time < max_wait_time:
            import asyncio
            await asyncio.sleep(5)  # 5초마다 체크
            wait_time += 5
            logging.info(f"Waiting for model to load... ({wait_time}s)")
        
        if model_manager.is_model_loaded(ModelType.LLAMA_3_1_8B.value):
            current_model = model_manager.get_current_model()
            if current_model:
                model, tokenizer = current_model
                logging.info("✅ Model loaded successfully!")
                logging.info(f"Model: {type(model).__name__}")
                logging.info(f"Tokenizer: {type(tokenizer).__name__}")
                logging.info(f"Current model: {model_manager.current_model}")
            else:
                logging.warning("⚠️ Model failed to load")
        else:
            logging.warning("⚠️ Model failed to load within timeout")
            logging.info("Server will run with basic responses only")
            
    except Exception as e:
        logging.error(f"Error during model loading: {str(e)}")
        logging.info("Server will run with basic responses only")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
    logging.info("Disconnected from MongoDB.")

@app.get("/")
async def root():
    model_status = "loaded" if is_model_ready() else "not loaded"
    return {
        "message": "AICounsel API is running",
        "llm_model_status": model_status
    }

@app.get("/health")
async def health_check():
    """서버 상태 및 모델 로딩 상태 확인"""
    model_status = "ready" if is_model_ready() else "not ready"
    
    return {
        "status": "healthy",
        "llm_model": model_status,
        "mongodb": "connected"
    } 
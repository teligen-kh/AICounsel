from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router
from app.api.v1.knowledge import router as knowledge_router
from .config import settings
from .database import connect_to_mongo, close_mongo_connection
from .api import chat, analysis
import logging

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

# 이벤트 핸들러
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    logging.info("Connected to MongoDB.")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
    logging.info("Disconnected from MongoDB.")

@app.get("/")
async def root():
    return {"message": "AICounsel API is running"} 
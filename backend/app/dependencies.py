from pymongo import MongoClient
from openai import AsyncOpenAI
from .core.config import settings
from .services.chat import ChatService

# MongoDB 클라이언트
client = MongoClient(settings.MONGODB_URL)
db = client[settings.DB_NAME]

# OpenAI 클라이언트
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ChatService 의존성
def get_chat_service() -> ChatService:
    return ChatService(db=db, openai_client=openai_client) 
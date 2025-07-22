"""
AICounsel 데이터베이스 연결 관리 모듈
MongoDB 연결 및 데이터베이스 인스턴스 관리
"""

from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging
from pymongo import IndexModel, ASCENDING, TEXT

# 전역 데이터베이스 연결 인스턴스
client = None  # MongoDB 클라이언트 인스턴스
db = None      # 데이터베이스 인스턴스

async def connect_to_mongo():
    """
    MongoDB 데이터베이스 연결을 초기화합니다.
    설정된 URL과 데이터베이스명으로 연결을 설정하고 연결 상태를 테스트합니다.
    """
    global client, db
    try:
        # MongoDB 클라이언트 생성 및 연결
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # 연결 상태 테스트 (ping 명령어)
        await client.admin.command('ping')
        logging.info("Successfully connected to MongoDB")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

async def close_mongo_connection():
    """
    MongoDB 데이터베이스 연결을 종료합니다.
    클라이언트 인스턴스가 존재하는 경우 연결을 안전하게 닫습니다.
    """
    global client
    if client is not None:
        client.close()  # MongoDB 클라이언트 연결 종료
        logging.info("MongoDB connection closed")

async def get_database():
    """
    데이터베이스 인스턴스를 반환합니다.
    연결이 없는 경우 자동으로 연결을 초기화합니다.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB 데이터베이스 인스턴스
    """
    global db
    if db is None:
        await connect_to_mongo()  # 연결이 없으면 초기화
    return db 
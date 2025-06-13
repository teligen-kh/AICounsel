from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging
from pymongo import IndexModel, ASCENDING, TEXT

client = None
db = None

async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB_NAME]
        # 연결 테스트
        await client.admin.command('ping')
        logging.info("Successfully connected to MongoDB")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

async def close_mongo_connection():
    global client
    if client is not None:
        client.close()
        logging.info("MongoDB connection closed")

async def get_database():
    global db
    if db is None:
        await connect_to_mongo()
    return db 
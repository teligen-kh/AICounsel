import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def delete_old_data():
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    collection = db.conversations

    # title이 None이 아닌 데이터 삭제
    result = await collection.delete_many({
        "title": {"$ne": None}
    })
    
    print(f"Deleted {result.deleted_count} documents")

if __name__ == "__main__":
    asyncio.run(delete_old_data()) 
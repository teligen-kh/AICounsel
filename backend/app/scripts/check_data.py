import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_data():
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    collection = db.conversations

    # 모든 문서 조회
    cursor = collection.find({})
    async for doc in cursor:
        print(f"Title: {doc.get('title')}")
        print(f"Fields: {list(doc.keys())}")
        print("---")

if __name__ == "__main__":
    asyncio.run(check_data()) 
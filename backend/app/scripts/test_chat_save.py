import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from pprint import pprint

async def test_chat_save():
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client['aicounsel']
    
    # 테스트 메시지
    test_message = {
        "content": "안녕하세요?",
        "role": "user",
        "session_id": "test_session_123",
        "timestamp": datetime.now()
    }
    
    # conversations 컬렉션에 저장
    result = await db.conversations.insert_one({
        "session_id": "test_session_123",
        "messages": [test_message],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "status": "in_progress"
    })
    
    print(f"저장된 문서 ID: {result.inserted_id}")
    
    # 저장된 내용 확인
    saved_doc = await db.conversations.find_one({"session_id": "test_session_123"})
    print("\n저장된 문서:")
    pprint(saved_doc)
    
    # 모든 컬렉션 확인
    collections = await db.list_collection_names()
    print(f"\n데이터베이스의 모든 컬렉션: {collections}")
    
    # 각 컬렉션의 문서 수 확인
    for collection_name in collections:
        count = await db[collection_name].count_documents({})
        print(f"{collection_name}: {count}개 문서")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_chat_save()) 
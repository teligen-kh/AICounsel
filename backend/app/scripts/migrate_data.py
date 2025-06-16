import asyncio
import sys
import os
from datetime import datetime
import re
from motor.motor_asyncio import AsyncIOMotorClient

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_database

def extract_consultation_time(title):
    # 파일명에서 날짜와 시간 추출 (YYYYMMDDHHMMSS 형식)
    match = re.search(r'\.(\d{14})$', title)
    if match:
        date_str = match.group(1)
        try:
            # YYYYMMDDHHMMSS 형식을 datetime 객체로 변환
            return datetime.strptime(date_str, '%Y%m%d%H%M%S')
        except ValueError:
            return None
    return None

async def migrate_data():
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    collection = db.conversations

    # utterances가 있는 문서 찾기
    cursor = collection.find({"utterances": {"$exists": True}})
    async for doc in cursor:
        # utterances를 messages로 변환
        messages = []
        for utterance in doc.get("utterances", []):
            message = {
                "role": "user" if utterance.get("speaker") == "고객" else "assistant",
                "content": utterance.get("text", ""),
                "timestamp": utterance.get("timestamp")
            }
            messages.append(message)

        # summary 생성
        summary = ""
        if messages:
            all_messages = [msg["content"] for msg in messages]
            summary = " ".join(all_messages)
            if len(summary) > 200:
                summary = summary[:200] + "..."

        # 문서 업데이트 - utterances는 유지하고 messages와 summary만 추가
        await collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "messages": messages,
                    "summary": summary
                }
            }
        )
        print(f"Updated document {doc['_id']}")

    print("Migration completed")

if __name__ == "__main__":
    asyncio.run(migrate_data()) 
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.chat import ChatMessage

class ChatService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.conversations

    async def save_message(self, message: ChatMessage):
        # 세션 ID로 대화 찾기
        conversation = await self.collection.find_one({"session_id": message.session_id})
        
        if conversation:
            # 기존 대화에 메시지 추가
            await self.collection.update_one(
                {"session_id": message.session_id},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.now()}
                }
            )
        else:
            # 새로운 대화 생성
            await self.collection.insert_one({
                "session_id": message.session_id,
                "messages": [message.dict()],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "status": "in_progress"
            })

    async def get_chat_history(
        self,
        session_id: str,
        limit: int = 50,
        before: Optional[datetime] = None
    ) -> List[ChatMessage]:
        # 대화 찾기
        conversation = await self.collection.find_one({"session_id": session_id})
        
        if not conversation:
            return []
        
        messages = conversation.get("messages", [])
        
        # before 날짜 이전의 메시지만 필터링
        if before:
            messages = [m for m in messages if m["timestamp"] < before]
        
        # 최신 메시지부터 limit 개수만큼 반환
        messages = sorted(messages, key=lambda x: x["timestamp"], reverse=True)[:limit]
        
        return [ChatMessage(**msg) for msg in messages]

    async def delete_chat_history(self, session_id: str) -> bool:
        result = await self.collection.delete_many({"session_id": session_id})
        return result.deleted_count > 0 
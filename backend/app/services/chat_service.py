from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from datetime import datetime
from ..models.chat import ChatMessage
from .llm_service import LLMService
import logging

class ChatService:
    def __init__(self, db: AsyncIOMotorDatabase, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm_service = llm_service
    
    async def process_message(self, message: str, conversation_id: Optional[str] = None) -> str:
        """
        사용자 메시지를 처리하고 응답을 생성합니다.
        
        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID (선택사항)
            
        Returns:
            생성된 응답
        """
        try:
            if not self.llm_service:
                raise ValueError("LLM service not initialized")
                
            # LLM 서비스를 통해 메시지 처리
            response = await self.llm_service.process_message(message, conversation_id)
            
            # 대화 기록 저장
            await self._save_conversation(message, response, conversation_id)
            
            return response
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            raise
    
    async def get_chat_history(self, session_id: str, limit: int = 50, before: Optional[datetime] = None) -> List[ChatMessage]:
        """
        특정 세션의 대화 기록을 조회합니다.
        
        Args:
            session_id: 세션 ID
            limit: 조회할 메시지 수
            before: 특정 시간 이전의 메시지만 조회
            
        Returns:
            대화 기록 리스트
        """
        try:
            query = {"session_id": session_id}
            if before:
                query["timestamp"] = {"$lt": before}
            
            cursor = self.db.chat_messages.find(query).sort("timestamp", -1).limit(limit)
            messages = await cursor.to_list(length=limit)
            
            # 시간순으로 정렬 (오래된 것부터)
            messages.reverse()
            
            return [ChatMessage(**msg) for msg in messages]
        except Exception as e:
            logging.error(f"Error getting chat history: {str(e)}")
            raise
    
    async def _save_conversation(self, user_message: str, assistant_response: str, conversation_id: Optional[str] = None):
        """
        대화 내용을 데이터베이스에 저장합니다.
        
        Args:
            user_message: 사용자 메시지
            assistant_response: 어시스턴트 응답
            conversation_id: 대화 ID
        """
        try:
            session_id = conversation_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            timestamp = datetime.now()
            
            # 사용자 메시지 저장
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=user_message,
                timestamp=timestamp
            )
            await self.db.chat_messages.insert_one(user_msg.dict())
            
            # 어시스턴트 응답 저장
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant", 
                content=assistant_response,
                timestamp=timestamp
            )
            await self.db.chat_messages.insert_one(assistant_msg.dict())
            
            logging.info(f"Conversation saved for session: {session_id}")
        except Exception as e:
            logging.error(f"Error saving conversation: {str(e)}")
            # 대화 저장 실패는 전체 프로세스를 중단하지 않도록 함
            pass
#!/usr/bin/env python3
"""
대화 맥락 관리 모듈
대화 세션을 관리하고 맥락 정보를 저장/복원
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class ConversationContextService:
    """대화 맥락 관리 서비스"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.context_collection = db.conversation_contexts
        self.session_timeout = timedelta(minutes=30)  # 30분 세션 타임아웃
    
    async def create_context(self, user_id: str, original_question: str) -> str:
        """새로운 대화 맥락 생성"""
        try:
            session_id = f"{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            context_data = {
                "user_id": user_id,
                "session_id": session_id,
                "original_question": original_question,
                "clarification_questions": [],
                "user_responses": [],
                "context_data": {},
                "status": "waiting_clarification",  # waiting_clarification, completed, expired
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "clarification_count": 0,
                "max_clarifications": 3
            }
            
            await self.context_collection.insert_one(context_data)
            logger.info(f"대화 맥락 생성: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"대화 맥락 생성 중 오류: {e}")
            return None
    
    async def get_context(self, session_id: str) -> Optional[Dict]:
        """대화 맥락 조회"""
        try:
            context = await self.context_collection.find_one({"session_id": session_id})
            
            if context:
                # 세션 타임아웃 체크
                if self._is_session_expired(context):
                    await self.expire_context(session_id)
                    return None
                
                return context
            
            return None
            
        except Exception as e:
            logger.error(f"대화 맥락 조회 중 오류: {e}")
            return None
    
    async def add_clarification_question(self, session_id: str, question: str) -> bool:
        """추가 질문 저장"""
        try:
            result = await self.context_collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"clarification_questions": question},
                    "$inc": {"clarification_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"추가 질문 저장: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"추가 질문 저장 중 오류: {e}")
            return False
    
    async def add_user_response(self, session_id: str, response: str) -> bool:
        """사용자 응답 저장"""
        try:
            result = await self.context_collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"user_responses": response},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"사용자 응답 저장: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"사용자 응답 저장 중 오류: {e}")
            return False
    
    async def update_context_data(self, session_id: str, key: str, value: Any) -> bool:
        """맥락 데이터 업데이트"""
        try:
            result = await self.context_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        f"context_data.{key}": value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"맥락 데이터 업데이트: {session_id} - {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"맥락 데이터 업데이트 중 오류: {e}")
            return False
    
    async def complete_context(self, session_id: str, final_answer: str) -> bool:
        """대화 맥락 완료"""
        try:
            result = await self.context_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "status": "completed",
                        "final_answer": final_answer,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"대화 맥락 완료: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"대화 맥락 완료 중 오류: {e}")
            return False
    
    async def expire_context(self, session_id: str) -> bool:
        """대화 맥락 만료"""
        try:
            result = await self.context_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "status": "expired",
                        "expired_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"대화 맥락 만료: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"대화 맥락 만료 중 오류: {e}")
            return False
    
    def _is_session_expired(self, context: Dict) -> bool:
        """세션이 만료되었는지 체크"""
        try:
            updated_at = context.get("updated_at")
            if not updated_at:
                return True
            
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
            return datetime.utcnow() - updated_at > self.session_timeout
            
        except Exception as e:
            logger.error(f"세션 만료 체크 중 오류: {e}")
            return True
    
    async def can_ask_more_clarifications(self, session_id: str) -> bool:
        """더 많은 추가 질문을 할 수 있는지 체크"""
        try:
            context = await self.get_context(session_id)
            if not context:
                return False
            
            clarification_count = context.get("clarification_count", 0)
            max_clarifications = context.get("max_clarifications", 3)
            
            return clarification_count < max_clarifications
            
        except Exception as e:
            logger.error(f"추가 질문 가능 여부 체크 중 오류: {e}")
            return False
    
    async def get_conversation_summary(self, session_id: str) -> Dict:
        """대화 요약 정보 반환"""
        try:
            context = await self.get_context(session_id)
            if not context:
                return {}
            
            return {
                "original_question": context.get("original_question"),
                "clarification_questions": context.get("clarification_questions", []),
                "user_responses": context.get("user_responses", []),
                "clarification_count": context.get("clarification_count", 0),
                "status": context.get("status"),
                "context_data": context.get("context_data", {})
            }
            
        except Exception as e:
            logger.error(f"대화 요약 조회 중 오류: {e}")
            return {}
    
    async def cleanup_expired_contexts(self) -> int:
        """만료된 대화 맥락 정리"""
        try:
            cutoff_time = datetime.utcnow() - self.session_timeout
            
            result = await self.context_collection.delete_many({
                "updated_at": {"$lt": cutoff_time},
                "status": {"$in": ["waiting_clarification", "expired"]}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"만료된 대화 맥락 {deleted_count}개 정리 완료")
            return deleted_count
            
        except Exception as e:
            logger.error(f"만료된 대화 맥락 정리 중 오류: {e}")
            return 0 
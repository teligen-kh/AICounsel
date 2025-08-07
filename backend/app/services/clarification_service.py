#!/usr/bin/env python3
"""
Clarification 서비스 모듈
모호한 질문에 대해 추가 질문을 생성하고 대화 맥락을 관리
"""

import logging
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from .ambiguity_detector import AmbiguityDetector
from .conversation_context_service import ConversationContextService
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class ClarificationService:
    """Clarification 서비스"""
    
    def __init__(self, db: AsyncIOMotorDatabase, llm_service: LLMService):
        self.db = db
        self.llm_service = llm_service
        self.ambiguity_detector = AmbiguityDetector()
        self.context_service = ConversationContextService(db)
    
    async def process_question(self, question: str, user_id: str, search_results: List[Dict] = None) -> Dict:
        """질문 처리 및 Clarification 필요 여부 판단"""
        try:
            # 1. 모호함 감지
            is_ambiguous = self.ambiguity_detector.is_ambiguous(question)
            
            # 2. 검색 결과가 없거나 모호한 경우 Clarification 필요
            needs_clarification = is_ambiguous or not search_results or len(search_results) == 0
            
            if needs_clarification:
                # 3. 대화 맥락 생성
                session_id = await self.context_service.create_context(user_id, question)
                
                # 4. 추가 질문 생성
                clarification_question = await self.generate_clarification_question(question, search_results)
                
                # 5. 추가 질문 저장
                await self.context_service.add_clarification_question(session_id, clarification_question)
                
                return {
                    "needs_clarification": True,
                    "session_id": session_id,
                    "clarification_question": clarification_question,
                    "reason": self.ambiguity_detector.get_ambiguity_reason(question) if is_ambiguous else "검색 결과 없음"
                }
            else:
                return {
                    "needs_clarification": False,
                    "search_results": search_results
                }
                
        except Exception as e:
            logger.error(f"질문 처리 중 오류: {e}")
            return {
                "needs_clarification": False,
                "error": str(e)
            }
    
    async def generate_clarification_question(self, original_question: str, search_results: List[Dict] = None) -> str:
        """추가 질문 생성"""
        try:
            # 모호함 이유 분석
            ambiguity_reason = self.ambiguity_detector.get_ambiguity_reason(original_question)
            missing_keywords = self.ambiguity_detector.get_missing_keywords(original_question)
            
            # LLM 프롬프트 생성
            prompt = f"""
다음 고객 질문에 대해 추가 정보를 얻기 위한 질문을 생성해주세요.

고객 질문: "{original_question}"
모호함 이유: {ambiguity_reason}
부족한 키워드: {', '.join(missing_keywords) if missing_keywords else '없음'}
검색 결과: {len(search_results) if search_results else 0}개

요구사항:
1. 공손하고 자연스러운 톤으로 작성
2. 구체적인 정보를 요청하는 질문
3. 예시를 포함하여 이해하기 쉽게
4. 1-2문장으로 간결하게

예시:
- "어떤 상품코드인지 알려주세요 (예: M3100처럼)"
- "구체적으로 어떤 기능을 원하시나요?"
- "어떤 고객의 견적서인지 알려주세요"

추가 질문:"""
            
            # LLM 호출
            clarification_question = await self.llm_service._handle_pure_llm_message(prompt)
            
            # 기본 질문 (LLM 실패 시)
            if not clarification_question or len(clarification_question.strip()) < 10:
                clarification_question = self._generate_fallback_question(original_question, missing_keywords)
            
            return clarification_question.strip()
            
        except Exception as e:
            logger.error(f"추가 질문 생성 중 오류: {e}")
            return self._generate_fallback_question(original_question, [])
    
    def _generate_fallback_question(self, original_question: str, missing_keywords: List[str]) -> str:
        """LLM 실패 시 기본 추가 질문 생성"""
        question_lower = original_question.lower()
        
        if '견적서' in question_lower:
            return "어떤 상품코드의 견적서인지 알려주세요."
        elif '직인' in question_lower:
            return "어떤 고객의 직인 설정인지 알려주세요."
        elif '설정' in question_lower:
            return "구체적으로 어떤 설정을 원하시나요?"
        elif '문제' in question_lower or '오류' in question_lower:
            return "어떤 기능에서 문제가 발생했는지 자세히 알려주세요."
        else:
            return "더 자세한 정보를 알려주시면 정확한 답변을 드릴 수 있습니다."
    
    async def process_clarification_response(self, session_id: str, user_response: str) -> Dict:
        """사용자의 Clarification 응답 처리"""
        try:
            # 1. 사용자 응답 저장
            await self.context_service.add_user_response(session_id, user_response)
            
            # 2. 대화 맥락 조회
            context = await self.context_service.get_context(session_id)
            if not context:
                return {
                    "error": "대화 맥락을 찾을 수 없습니다.",
                    "needs_clarification": False
                }
            
            # 3. 원래 질문과 사용자 응답을 결합하여 새로운 질문 생성
            original_question = context.get("original_question", "")
            combined_question = f"{original_question} {user_response}"
            
            # 4. 다시 모호함 체크
            is_still_ambiguous = self.ambiguity_detector.is_ambiguous(combined_question)
            
            # 5. 추가 질문 가능 여부 체크
            can_ask_more = await self.context_service.can_ask_more_clarifications(session_id)
            
            if is_still_ambiguous and can_ask_more:
                # 6. 추가 질문 생성
                clarification_question = await self.generate_clarification_question(combined_question)
                await self.context_service.add_clarification_question(session_id, clarification_question)
                
                return {
                    "needs_clarification": True,
                    "session_id": session_id,
                    "clarification_question": clarification_question,
                    "reason": "추가 정보가 필요합니다."
                }
            else:
                # 7. 최종 질문으로 처리 준비
                return {
                    "needs_clarification": False,
                    "final_question": combined_question,
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"Clarification 응답 처리 중 오류: {e}")
            return {
                "error": str(e),
                "needs_clarification": False
            }
    
    async def generate_final_response(self, session_id: str, search_results: List[Dict]) -> str:
        """최종 응답 생성"""
        try:
            # 1. 대화 맥락 조회
            context = await self.context_service.get_context(session_id)
            if not context:
                return "죄송합니다. 대화 맥락을 찾을 수 없습니다."
            
            # 2. 대화 요약 생성
            conversation_summary = await self.context_service.get_conversation_summary(session_id)
            
            # 3. LLM을 사용하여 최종 응답 생성
            prompt = f"""
다음 대화 내용을 바탕으로 고객에게 친절하고 정확한 답변을 제공해주세요.

대화 요약:
- 원래 질문: {conversation_summary.get('original_question')}
- 추가 질문들: {conversation_summary.get('clarification_questions')}
- 사용자 응답들: {conversation_summary.get('user_responses')}

검색 결과: {len(search_results)}개

요구사항:
1. 대화 맥락을 고려한 자연스러운 응답
2. 친근하고 도움이 되는 톤
3. 구체적인 단계나 방법이 있다면 명확하게 설명
4. "도움이 되셨나요?" 같은 마무리 포함

답변:"""
            
            final_response = await self.llm_service._handle_pure_llm_message(prompt)
            
            # 4. 대화 맥락 완료
            await self.context_service.complete_context(session_id, final_response)
            
            return final_response.strip()
            
        except Exception as e:
            logger.error(f"최종 응답 생성 중 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    async def get_clarification_status(self, session_id: str) -> Dict:
        """Clarification 상태 조회"""
        try:
            context = await self.context_service.get_context(session_id)
            if not context:
                return {"error": "대화 맥락을 찾을 수 없습니다."}
            
            return {
                "session_id": session_id,
                "status": context.get("status"),
                "clarification_count": context.get("clarification_count", 0),
                "max_clarifications": context.get("max_clarifications", 3),
                "can_ask_more": await self.context_service.can_ask_more_clarifications(session_id)
            }
            
        except Exception as e:
            logger.error(f"Clarification 상태 조회 중 오류: {e}")
            return {"error": str(e)} 
#!/usr/bin/env python3
"""
Clarification 기능 테스트 모듈
모호한 질문에 대한 추가 질문 생성과 대화 맥락 관리를 테스트
"""

import asyncio
import motor.motor_asyncio
import logging
from typing import List, Dict, Optional
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.clarification_service import ClarificationService
from app.services.conversation_context_service import ConversationContextService
from app.services.ambiguity_detector import AmbiguityDetector
from app.services.llm_service import LLMService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClarificationTester:
    """Clarification 기능 테스트기"""
    
    def __init__(self, db, llm_service):
        self.db = db
        self.llm_service = llm_service
        self.clarification_service = ClarificationService(db, llm_service)
        self.context_service = ConversationContextService(db)
        self.ambiguity_detector = AmbiguityDetector()
        
    async def test_ambiguity_detection(self, test_questions: List[str]):
        """모호함 감지 테스트"""
        logger.info("=== 모호함 감지 테스트 시작 ===")
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                # 모호함 감지
                is_ambiguous = self.ambiguity_detector.is_ambiguous(question)
                reason = self.ambiguity_detector.get_ambiguity_reason(question)
                missing_keywords = self.ambiguity_detector.get_missing_keywords(question)
                
                logger.info(f"모호함 여부: {is_ambiguous}")
                logger.info(f"모호함 이유: {reason}")
                logger.info(f"부족한 키워드: {missing_keywords}")
                
            except Exception as e:
                logger.error(f"모호함 감지 테스트 {i} 실행 중 오류: {e}")
        
        logger.info("\n=== 모호함 감지 테스트 완료 ===")
    
    async def test_clarification_question_generation(self, test_questions: List[str]):
        """추가 질문 생성 테스트"""
        logger.info("=== 추가 질문 생성 테스트 시작 ===")
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                # 추가 질문 생성
                clarification_question = await self.clarification_service.generate_clarification_question(question)
                
                logger.info(f"원래 질문: {question}")
                logger.info(f"추가 질문: {clarification_question}")
                
            except Exception as e:
                logger.error(f"추가 질문 생성 테스트 {i} 실행 중 오류: {e}")
        
        logger.info("\n=== 추가 질문 생성 테스트 완료 ===")
    
    async def test_conversation_context(self, test_questions: List[str]):
        """대화 맥락 관리 테스트"""
        logger.info("=== 대화 맥락 관리 테스트 시작 ===")
        
        user_id = "test_user_001"
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                # 1. 대화 맥락 생성
                session_id = await self.context_service.create_context(user_id, question)
                logger.info(f"세션 ID 생성: {session_id}")
                
                # 2. 추가 질문 생성 및 저장
                clarification_question = await self.clarification_service.generate_clarification_question(question)
                await self.context_service.add_clarification_question(session_id, clarification_question)
                logger.info(f"추가 질문 저장: {clarification_question}")
                
                # 3. 사용자 응답 시뮬레이션
                user_response = f"테스트 응답 {i}"
                await self.context_service.add_user_response(session_id, user_response)
                logger.info(f"사용자 응답 저장: {user_response}")
                
                # 4. 대화 요약 조회
                summary = await self.context_service.get_conversation_summary(session_id)
                logger.info(f"대화 요약: {summary}")
                
                # 5. 대화 맥락 완료
                final_answer = f"테스트 최종 답변 {i}"
                await self.context_service.complete_context(session_id, final_answer)
                logger.info(f"대화 맥락 완료: {final_answer}")
                
            except Exception as e:
                logger.error(f"대화 맥락 관리 테스트 {i} 실행 중 오류: {e}")
        
        logger.info("\n=== 대화 맥락 관리 테스트 완료 ===")
    
    async def test_full_clarification_flow(self, test_questions: List[str]):
        """전체 Clarification 플로우 테스트"""
        logger.info("=== 전체 Clarification 플로우 테스트 시작 ===")
        
        user_id = "test_user_002"
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                # 1. 질문 처리 및 Clarification 필요 여부 판단
                clarification_result = await self.clarification_service.process_question(question, user_id)
                
                logger.info(f"Clarification 필요 여부: {clarification_result.get('needs_clarification')}")
                
                if clarification_result.get("needs_clarification"):
                    session_id = clarification_result.get("session_id")
                    clarification_question = clarification_result.get("clarification_question")
                    reason = clarification_result.get("reason")
                    
                    logger.info(f"세션 ID: {session_id}")
                    logger.info(f"추가 질문: {clarification_question}")
                    logger.info(f"이유: {reason}")
                    
                    # 2. 사용자 응답 시뮬레이션
                    user_response = f"상품코드 M3100입니다"
                    
                    # 3. Clarification 응답 처리
                    response_result = await self.clarification_service.process_clarification_response(session_id, user_response)
                    
                    logger.info(f"응답 처리 결과: {response_result}")
                    
                    if response_result.get("needs_clarification"):
                        # 추가 Clarification 필요
                        additional_question = response_result.get("clarification_question")
                        logger.info(f"추가 Clarification 필요: {additional_question}")
                        
                        # 두 번째 사용자 응답
                        second_response = "네, 맞습니다"
                        second_result = await self.clarification_service.process_clarification_response(session_id, second_response)
                        logger.info(f"두 번째 응답 처리 결과: {second_result}")
                        
                        if not second_result.get("needs_clarification"):
                            # 최종 응답 생성
                            final_question = second_result.get("final_question")
                            logger.info(f"최종 질문: {final_question}")
                            
                            # 최종 응답 생성 (시뮬레이션)
                            search_results = [{"answer": "견적서 단위 변경은 상품코드 정보관리에서 가능합니다.", "score": 1.0}]
                            final_response = await self.clarification_service.generate_final_response(session_id, search_results)
                            logger.info(f"최종 응답: {final_response}")
                    else:
                        # 최종 질문으로 처리
                        final_question = response_result.get("final_question")
                        logger.info(f"최종 질문: {final_question}")
                        
                        # 최종 응답 생성 (시뮬레이션)
                        search_results = [{"answer": "견적서 단위 변경은 상품코드 정보관리에서 가능합니다.", "score": 1.0}]
                        final_response = await self.clarification_service.generate_final_response(session_id, search_results)
                        logger.info(f"최종 응답: {final_response}")
                else:
                    logger.info("Clarification 불필요 - 직접 처리")
                
            except Exception as e:
                logger.error(f"전체 Clarification 플로우 테스트 {i} 실행 중 오류: {e}")
        
        logger.info("\n=== 전체 Clarification 플로우 테스트 완료 ===")

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # LLM 서비스 초기화
        llm_service = LLMService()
        logger.info("LLM 서비스 초기화 완료")
        
        # 테스트기 생성
        tester = ClarificationTester(db, llm_service)
        
        # 테스트 질문들 (모호한 질문들)
        test_questions = [
            "견적서 단위 바꾸고 싶어",
            "이거 안돼",
            "설정하고 싶은데",
            "문제가 있어",
            "어떻게 하면 되나요?",
            "직인 설정",
            "매출 작업",
            "이런 식으로 하고 싶어"
        ]
        
        # 1. 모호함 감지 테스트
        await tester.test_ambiguity_detection(test_questions)
        
        # 2. 추가 질문 생성 테스트
        await tester.test_clarification_question_generation(test_questions)
        
        # 3. 대화 맥락 관리 테스트
        await tester.test_conversation_context(test_questions[:3])  # 처음 3개만 테스트
        
        # 4. 전체 Clarification 플로우 테스트
        await tester.test_full_clarification_flow(test_questions[:2])  # 처음 2개만 테스트
        
        logger.info("🎉 Clarification 기능 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
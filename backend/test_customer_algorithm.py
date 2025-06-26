#!/usr/bin/env python3
"""
고객 응대 알고리즘 테스트 스크립트
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_algorithm import ConversationAlgorithm
from app.services.llm_service import LLMService
from app.services.mongodb_search_service import MongoDBSearchService
from app.core.database import get_database, connect_to_mongo, close_mongo_connection

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('customer_algorithm_test.log'),
        logging.StreamHandler()
    ]
)

class CustomerAlgorithmTester:
    def __init__(self):
        self.conversation_algorithm = ConversationAlgorithm()
        self.llm_service = None
        self.search_service = None
        
    async def setup_services(self):
        """서비스들을 초기화합니다."""
        try:
            # 데이터베이스 연결 초기화
            await connect_to_mongo()
            logging.info("MongoDB 연결 완료")
            
            # 데이터베이스 연결
            db = get_database()
            
            # LLM 서비스 초기화
            self.llm_service = LLMService(db, use_db_priority=True)
            
            # MongoDB 검색 서비스 초기화
            self.search_service = MongoDBSearchService(db)
            
            logging.info("서비스 초기화 완료")
            
        except Exception as e:
            logging.error(f"서비스 초기화 실패: {str(e)}")
            raise
    
    def test_conversation_classification(self):
        """대화 분류 테스트"""
        logging.info("=" * 60)
        logging.info("대화 분류 테스트")
        logging.info("=" * 60)
        
        test_cases = [
            # 일상 대화 테스트
            ("안녕하세요", "casual"),
            ("좋은 하루 되세요", "casual"),
            ("감사합니다", "casual"),
            ("고생하세요", "casual"),
            ("화이팅!", "casual"),
            ("오늘 날씨가 좋네요", "casual"),
            
            # 전문 상담 테스트
            ("프린터가 작동 안 해요", "professional"),
            ("포스 설치 방법 알려주세요", "professional"),
            ("데이터베이스 오류가 발생했어요", "professional"),
            ("상품 검색이 안돼요", "professional"),
            ("인터넷 연결 문제가 있어요", "professional"),
            ("결제 오류가 발생했어요", "professional"),
            ("어떻게 해결하나요?", "professional"),
            ("설정 방법을 알려주세요", "professional"),
        ]
        
        correct = 0
        total = len(test_cases)
        
        for message, expected in test_cases:
            result = self.conversation_algorithm.classify_conversation_type(message)
            status = "[OK]" if result == expected else "[FAIL]"
            logging.info(f"{status} 입력: '{message}' -> 예상: {expected}, 실제: {result}")
            
            if result == expected:
                correct += 1
        
        accuracy = (correct / total) * 100
        logging.info(f"정확도: {correct}/{total} ({accuracy:.1f}%)")
        
        return accuracy >= 80  # 80% 이상이면 성공
    
    async def test_casual_conversation(self):
        """일상 대화 처리 테스트"""
        logging.info("=" * 60)
        logging.info("일상 대화 처리 테스트")
        logging.info("=" * 60)
        
        test_messages = [
            "안녕하세요",
            "좋은 하루 되세요",
            "감사합니다",
            "고생하세요",
            "화이팅!",
            "오늘 날씨가 좋네요"
        ]
        
        for message in test_messages:
            logging.info(f"테스트 메시지: '{message}'")
            
            # 기본 응답 테스트
            basic_response = self.conversation_algorithm._generate_casual_response(message)
            logging.info(f"기본 응답: {basic_response}")
            
            # LLaMA 응답 테스트 (모델이 있는 경우)
            if self.llm_service and self.llm_service.model and self.llm_service.tokenizer:
                try:
                    llama_response = await self.conversation_algorithm._generate_llama_casual_response(
                        message, self.llm_service.model, self.llm_service.tokenizer
                    )
                    logging.info(f"LLaMA 응답: {llama_response}")
                except Exception as e:
                    logging.error(f"LLaMA 응답 생성 실패: {str(e)}")
            
            logging.info("-" * 40)
    
    async def test_professional_conversation(self):
        """전문 상담 처리 테스트"""
        logging.info("=" * 60)
        logging.info("전문 상담 처리 테스트")
        logging.info("=" * 60)
        
        test_messages = [
            "프린터가 작동 안 해요",
            "포스 설치 방법 알려주세요",
            "데이터베이스 오류가 발생했어요",
            "상품 검색이 안돼요",
            "인터넷 연결 문제가 있어요"
        ]
        
        for message in test_messages:
            logging.info(f"테스트 메시지: '{message}'")
            
            # DB 검색 테스트
            if self.search_service:
                try:
                    db_answer = await self.search_service.search_answer(message)
                    if db_answer:
                        logging.info(f"DB 답변: {db_answer[:200]}...")
                        
                        # LLaMA 정리 테스트 (모델이 있는 경우)
                        if self.llm_service and self.llm_service.model and self.llm_service.tokenizer:
                            try:
                                llama_response = await self.conversation_algorithm._generate_llama_professional_response(
                                    message, db_answer, self.llm_service.model, self.llm_service.tokenizer
                                )
                                logging.info(f"LLaMA 정리: {llama_response[:200]}...")
                            except Exception as e:
                                logging.error(f"LLaMA 정리 실패: {str(e)}")
                        
                        # 기본 포맷팅 테스트
                        formatted = self.conversation_algorithm._format_db_answer(db_answer, message)
                        logging.info(f"포맷팅: {formatted[:200]}...")
                    else:
                        logging.info("DB 답변 없음")
                        no_answer = self.conversation_algorithm.generate_no_answer_response(message)
                        logging.info(f"상담사 연락 안내: {no_answer[:200]}...")
                        
                except Exception as e:
                    logging.error(f"DB 검색 실패: {str(e)}")
            
            logging.info("-" * 40)
    
    async def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        logging.info("=" * 60)
        logging.info("전체 워크플로우 테스트")
        logging.info("=" * 60)
        
        test_messages = [
            "안녕하세요",  # 일상 대화
            "프린터가 작동 안 해요",  # 전문 상담
            "감사합니다",  # 일상 대화
            "포스 설치 방법 알려주세요",  # 전문 상담
            "화이팅!",  # 일상 대화
            "데이터베이스 오류가 발생했어요"  # 전문 상담
        ]
        
        for message in test_messages:
            logging.info(f"전체 워크플로우 테스트: '{message}'")
            
            if self.llm_service:
                try:
                    response = await self.llm_service.process_message(message)
                    logging.info(f"최종 응답: {response[:300]}...")
                except Exception as e:
                    logging.error(f"전체 워크플로우 실패: {str(e)}")
            
            logging.info("-" * 40)
    
    async def run_all_tests(self):
        """모든 테스트를 실행합니다."""
        logging.info("고객 응대 알고리즘 테스트 시작")
        logging.info(f"테스트 시작 시간: {datetime.now()}")
        
        try:
            # 서비스 초기화
            await self.setup_services()
            
            # 테스트 실행
            classification_success = self.test_conversation_classification()
            
            await self.test_casual_conversation()
            await self.test_professional_conversation()
            await self.test_full_workflow()
            
            # 통계 출력
            if self.llm_service:
                self.llm_service.log_response_stats()
            
            logging.info("=" * 60)
            logging.info("테스트 완료")
            logging.info(f"테스트 종료 시간: {datetime.now()}")
            
            if classification_success:
                logging.info("✓ 대화 분류 테스트 성공")
            else:
                logging.warning("⚠ 대화 분류 테스트 정확도 부족")
            
        except Exception as e:
            logging.error(f"테스트 실행 중 오류 발생: {str(e)}")
            raise
        finally:
            # 데이터베이스 연결 종료
            await close_mongo_connection()

async def main():
    """메인 함수"""
    tester = CustomerAlgorithmTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
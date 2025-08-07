#!/usr/bin/env python3
"""
context_patterns를 활용한 분류 테스트 스크립트
"""

import asyncio
import motor.motor_asyncio
import logging
import sys
import os

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.context_aware_classifier import ContextAwareClassifier

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextPatternsTester:
    """context_patterns 분류 테스터"""
    
    def __init__(self, db):
        self.db = db
        self.classifier = ContextAwareClassifier(db)
        
    async def test_classification(self, test_questions: list):
        """테스트 질문들에 대한 분류를 테스트합니다."""
        try:
            logger.info("=== context_patterns 분류 테스트 시작 ===")
            
            results = []
            
            for i, question in enumerate(test_questions, 1):
                logger.info(f"\n--- 테스트 {i}: {question} ---")
                
                # 분류 실행
                input_type, details = await self.classifier.classify_input(question)
                
                logger.info(f"분류 결과: {input_type.value}")
                logger.info(f"분류 상세: {details}")
                
                results.append({
                    'question': question,
                    'input_type': input_type.value,
                    'details': details
                })
            
            # 결과 요약
            logger.info("\n=== 테스트 결과 요약 ===")
            technical_count = sum(1 for r in results if r['input_type'] == 'technical')
            casual_count = sum(1 for r in results if r['input_type'] == 'casual')
            unknown_count = sum(1 for r in results if r['input_type'] == 'unknown')
            
            logger.info(f"Technical 분류: {technical_count}개")
            logger.info(f"Casual 분류: {casual_count}개")
            logger.info(f"Unknown 분류: {unknown_count}개")
            
            return results
            
        except Exception as e:
            logger.error(f"분류 테스트 중 오류: {e}")
            return []

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # 테스터 생성
        tester = ContextPatternsTester(db)
        
        # 테스트 질문들
        test_questions = [
            # Technical 질문들 (context_patterns에서 매칭되어야 함)
            "프린터 용지 출력이 안되고 빨간 불이 깜빡이는 문제",
            "POS 시스템 백업 방법",
            "프로그램 재설치문의",
            "판매관리비 코드관리에서 계정 항목이 안보인다고 하심",
            "클라우드 설치요청",
            "바코드프린터 새로 구매했어요 설치요청 드립니다",
            "상품엑셀 저장이 안됩니다",
            "쇼핑몰을 저희가 확인하는 방법?",
            "매출작업을 해놧는데 손님이 해당매출을 한개로 만들어달라고하는데 매출을 합칠수있나요?",
            "키오스크에서 카드결제를 하는중 통신에러 통신실패라고 나온다고 하는데 무슨문제인가요?",
            
            # Casual 질문들 (technical로 분류되지 않아야 함)
            "안녕하세요?",
            "바쁘실텐데 수고 많으십니다",
            "어? 사람이 아닌가요?",
            "AI구나. 상담사 연결",
            "오늘 날씨가 좋네요",
            "점심 먹으셨나요?",
            "감사합니다",
            "잘 지내세요",
            
            # Unknown 질문들 (매칭되지 않을 수 있는 것들)
            "한국 역사에 대해 알려주세요",
            "요리 레시피를 알려주세요",
            "운동하는 방법을 알려주세요",
            "여행지 추천해주세요"
        ]
        
        # 분류 테스트 실행
        results = await tester.test_classification(test_questions)
        
        logger.info(f"\n🎉 테스트 완료! 총 {len(results)}개 질문 테스트됨")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
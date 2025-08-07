#!/usr/bin/env python3
"""
context_patterns의 품질을 확인하고 잘못된 패턴들을 찾는 스크립트
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

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextPatternsQualityChecker:
    """context_patterns 품질 검사기"""
    
    def __init__(self, db):
        self.db = db
        self.pattern_collection = db.context_patterns
        
    async def check_patterns_quality(self):
        """패턴들의 품질을 확인합니다."""
        try:
            logger.info("=== context_patterns 품질 검사 시작 ===")
            
            # 전체 문서 수 확인
            total_count = await self.pattern_collection.count_documents({})
            logger.info(f"전체 패턴 수: {total_count}")
            
            # 모든 패턴 가져오기
            all_patterns = await self.pattern_collection.find({}).to_list(length=None)
            
            # 품질 분석
            good_patterns = []
            bad_patterns = []
            
            # 잘못된 패턴을 식별하는 키워드들
            bad_keywords = [
                "이런 경우에 대한 정확한 정보를 제공할 수 없습니다",
                "키워드를 추출해 드",
                "기술적 문제나 상담과 관련된",
                "추출된 키워드들",
                "다음 질문에서",
                "쉼표로 구분해서",
                "답변해주세요",
                "제외해주세요",
                "질문:",
                "추출된 키워드들:"
            ]
            
            for pattern_doc in all_patterns:
                pattern = pattern_doc.get('pattern', '')
                
                # 잘못된 패턴인지 확인
                is_bad = False
                for bad_keyword in bad_keywords:
                    if bad_keyword in pattern:
                        is_bad = True
                        break
                
                # 패턴 길이 확인 (너무 긴 패턴은 의심)
                if len(pattern) > 50:
                    is_bad = True
                
                # 문장 끝 확인 (마침표, 느낌표 등이 있으면 의심)
                if pattern.endswith(('.', '!', '?')):
                    is_bad = True
                
                if is_bad:
                    bad_patterns.append(pattern_doc)
                else:
                    good_patterns.append(pattern_doc)
            
            # 결과 출력
            logger.info(f"✅ 좋은 패턴 수: {len(good_patterns)}")
            logger.info(f"❌ 나쁜 패턴 수: {len(bad_patterns)}")
            
            # 나쁜 패턴 샘플 출력
            if bad_patterns:
                logger.info("\n=== 나쁜 패턴 샘플 (최대 10개) ===")
                for i, bad_pattern in enumerate(bad_patterns[:10], 1):
                    pattern = bad_pattern.get('pattern', '')
                    logger.info(f"{i}. {pattern}")
                
                if len(bad_patterns) > 10:
                    logger.info(f"... 외 {len(bad_patterns) - 10}개 더")
            
            # 좋은 패턴 샘플 출력
            if good_patterns:
                logger.info("\n=== 좋은 패턴 샘플 (최대 10개) ===")
                for i, good_pattern in enumerate(good_patterns[:10], 1):
                    pattern = good_pattern.get('pattern', '')
                    logger.info(f"{i}. {pattern}")
                
                if len(good_patterns) > 10:
                    logger.info(f"... 외 {len(good_patterns) - 10}개 더")
            
            return len(good_patterns), len(bad_patterns)
            
        except Exception as e:
            logger.error(f"품질 검사 중 오류: {e}")
            return 0, 0

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # 품질 검사기 생성
        checker = ContextPatternsQualityChecker(db)
        
        # 품질 검사 실행
        good_count, bad_count = await checker.check_patterns_quality()
        
        logger.info(f"\n=== 최종 결과 ===")
        logger.info(f"좋은 패턴: {good_count}개")
        logger.info(f"나쁜 패턴: {bad_count}개")
        
        if bad_count > 0:
            logger.warning(f"⚠️ 나쁜 패턴이 {bad_count}개 발견되었습니다. 정리가 필요합니다.")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
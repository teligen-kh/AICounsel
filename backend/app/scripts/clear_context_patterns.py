#!/usr/bin/env python3
"""
context_patterns 테이블의 모든 데이터를 삭제하는 스크립트
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

class ContextPatternsCleaner:
    """context_patterns 테이블 정리기"""
    
    def __init__(self, db):
        self.db = db
        self.pattern_collection = db.context_patterns
        
    async def get_current_count(self) -> int:
        """현재 context_patterns 테이블의 문서 수를 가져옵니다."""
        try:
            count = await self.pattern_collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"문서 수 확인 실패: {e}")
            return 0
    
    async def clear_all_patterns(self) -> bool:
        """context_patterns 테이블의 모든 데이터를 삭제합니다."""
        try:
            # 삭제 전 문서 수 확인
            before_count = await self.get_current_count()
            logger.info(f"삭제 전 context_patterns 문서 수: {before_count}")
            
            if before_count == 0:
                logger.info("context_patterns 테이블이 이미 비어있습니다.")
                return True
            
            # 모든 문서 삭제
            result = await self.pattern_collection.delete_many({})
            deleted_count = result.deleted_count
            
            # 삭제 후 문서 수 확인
            after_count = await self.get_current_count()
            
            logger.info(f"삭제된 문서 수: {deleted_count}")
            logger.info(f"삭제 후 context_patterns 문서 수: {after_count}")
            
            if after_count == 0:
                logger.info("✅ context_patterns 테이블 정리 완료!")
                return True
            else:
                logger.error(f"❌ 일부 문서가 남아있습니다: {after_count}개")
                return False
                
        except Exception as e:
            logger.error(f"context_patterns 삭제 중 오류: {e}")
            return False
    
    async def show_sample_patterns(self, limit: int = 5):
        """삭제 전 샘플 패턴들을 보여줍니다."""
        try:
            sample_patterns = await self.pattern_collection.find({}).limit(limit).to_list(length=limit)
            
            if sample_patterns:
                logger.info(f"삭제될 샘플 패턴들 (최대 {limit}개):")
                for i, pattern in enumerate(sample_patterns, 1):
                    logger.info(f"  {i}. {pattern.get('pattern', 'N/A')} ({pattern.get('context', 'N/A')})")
            else:
                logger.info("삭제할 패턴이 없습니다.")
                
        except Exception as e:
            logger.error(f"샘플 패턴 조회 실패: {e}")

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # 정리기 생성
        cleaner = ContextPatternsCleaner(db)
        
        # 삭제 전 샘플 패턴 보기
        await cleaner.show_sample_patterns(5)
        
        # 자동으로 모든 패턴 삭제
        logger.info("context_patterns 테이블의 모든 데이터를 삭제합니다...")
        success = await cleaner.clear_all_patterns()
        
        if success:
            logger.info("✅ context_patterns 테이블 정리 완료!")
        else:
            logger.error("❌ context_patterns 테이블 정리 실패!")
            
    except Exception as e:
        logger.error(f"스크립트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
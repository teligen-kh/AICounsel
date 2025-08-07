#!/usr/bin/env python3
"""
나쁜 패턴들을 식별하고 삭제하는 스크립트
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

class BadPatternsCleaner:
    """나쁜 패턴 정리기"""
    
    def __init__(self, db):
        self.db = db
        self.pattern_collection = db.context_patterns
        
    def is_bad_pattern(self, pattern: str) -> bool:
        """패턴이 나쁜 패턴인지 판단합니다."""
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
            "추출된 키워드들:",
            "다음 키워드를 기술적 문제나 상담에 관련하여 추출하였습니다",
            "백업 재료를 의미하는 것으로 추정되는",
            "설명서 (데모란 제품이나 서비스의 시연을 의미하는 용어이"
        ]
        
        # 너무 짧거나 일반적인 단어들
        too_short_or_general = [
            "네", "팀", "대표", "직인", "삭제", "통신", "자동전환", "검수포스", "자사몰"
        ]
        
        # 문장 부호로 끝나는 패턴
        if pattern.endswith(('.', '!', '?')):
            return True
            
        # 너무 긴 패턴 (50자 이상)
        if len(pattern) > 50:
            return True
            
        # 나쁜 키워드 포함
        for bad_keyword in bad_keywords:
            if bad_keyword in pattern:
                return True
                
        # 너무 짧거나 일반적인 단어
        if pattern in too_short_or_general:
            return True
            
        # 특정 인명 (대리, 팀장 등이 포함된 경우)
        if any(name in pattern for name in ["대리", "팀장", "나성수"]):
            return True
            
        return False
    
    async def find_and_clean_bad_patterns(self):
        """나쁜 패턴들을 찾아서 삭제합니다."""
        try:
            logger.info("=== 나쁜 패턴 정리 시작 ===")
            
            # 전체 문서 수 확인
            total_count = await self.pattern_collection.count_documents({})
            logger.info(f"전체 패턴 수: {total_count}")
            
            # 모든 패턴 가져오기
            all_patterns = await self.pattern_collection.find({}).to_list(length=None)
            
            # 나쁜 패턴 식별
            bad_patterns = []
            good_patterns = []
            
            for pattern_doc in all_patterns:
                pattern = pattern_doc.get('pattern', '')
                
                if self.is_bad_pattern(pattern):
                    bad_patterns.append(pattern_doc)
                else:
                    good_patterns.append(pattern_doc)
            
            logger.info(f"✅ 좋은 패턴 수: {len(good_patterns)}")
            logger.info(f"❌ 나쁜 패턴 수: {len(bad_patterns)}")
            
            # 나쁜 패턴 샘플 출력
            if bad_patterns:
                logger.info("\n=== 삭제될 나쁜 패턴 샘플 (최대 10개) ===")
                for i, bad_pattern in enumerate(bad_patterns[:10], 1):
                    pattern = bad_pattern.get('pattern', '')
                    logger.info(f"{i}. {pattern}")
                
                if len(bad_patterns) > 10:
                    logger.info(f"... 외 {len(bad_patterns) - 10}개 더")
            
            # 나쁜 패턴들 삭제
            if bad_patterns:
                logger.info(f"\n=== 나쁜 패턴 {len(bad_patterns)}개 삭제 중... ===")
                
                # 나쁜 패턴들의 ObjectID 수집
                bad_object_ids = [pattern_doc['_id'] for pattern_doc in bad_patterns]
                
                # 삭제 실행
                result = await self.pattern_collection.delete_many({"_id": {"$in": bad_object_ids}})
                deleted_count = result.deleted_count
                
                logger.info(f"삭제 완료: {deleted_count}개의 패턴이 삭제됨")
                
                # 최종 확인
                final_count = await self.pattern_collection.count_documents({})
                logger.info(f"최종 context_patterns 문서 수: {final_count}")
                
                return deleted_count
            else:
                logger.info("삭제할 나쁜 패턴이 없습니다.")
                return 0
                
        except Exception as e:
            logger.error(f"나쁜 패턴 정리 중 오류: {e}")
            return 0

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # 나쁜 패턴 정리기 생성
        cleaner = BadPatternsCleaner(db)
        
        # 나쁜 패턴 정리 실행
        deleted_count = await cleaner.find_and_clean_bad_patterns()
        
        if deleted_count > 0:
            logger.info(f"🎉 {deleted_count}개의 나쁜 패턴이 성공적으로 삭제되었습니다!")
        else:
            logger.info("✅ 삭제할 나쁜 패턴이 없었습니다.")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
여러 ObjectID의 문서들을 확인하는 스크립트
"""

import asyncio
import motor.motor_asyncio
import logging
from bson import ObjectId
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

async def check_multiple_documents(object_ids: list):
    """여러 ObjectID의 문서들을 확인합니다."""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # context_patterns 컬렉션
        pattern_collection = db.context_patterns
        
        logger.info(f"=== {len(object_ids)}개의 ObjectID 확인 시작 ===")
        
        found_count = 0
        not_found_count = 0
        
        for i, object_id_str in enumerate(object_ids, 1):
            try:
                # ObjectID 변환
                object_id = ObjectId(object_id_str)
                
                # 문서 검색
                document = await pattern_collection.find_one({"_id": object_id})
                
                if document:
                    found_count += 1
                    pattern = document.get('pattern', 'N/A')
                    context = document.get('context', 'N/A')
                    
                    logger.info(f"{i}. ObjectID: {object_id_str}")
                    logger.info(f"   패턴: {pattern}")
                    logger.info(f"   컨텍스트: {context}")
                    logger.info("-" * 80)
                else:
                    not_found_count += 1
                    logger.warning(f"{i}. ObjectID: {object_id_str} - 문서를 찾을 수 없습니다")
                    logger.info("-" * 80)
                    
            except Exception as e:
                logger.error(f"{i}. ObjectID: {object_id_str} - 확인 중 오류: {e}")
                logger.info("-" * 80)
        
        logger.info(f"=== 확인 완료 ===")
        logger.info(f"찾은 문서: {found_count}개")
        logger.info(f"찾지 못한 문서: {not_found_count}개")
        
    except Exception as e:
        logger.error(f"문서 확인 중 오류: {e}")

async def main():
    """메인 함수"""
    object_ids = [
        "689394ef7ba62b237b236d19",
        "689394ef7ba62b237b236d22",
        "689394ef7ba62b237b236d25",
        "689394ef7ba62b237b236d28",
        "689394ef7ba62b237b236d3a",
        "689394ef7ba62b237b236d43",
        "689394ef7ba62b237b236d46",
        "689394ef7ba62b237b236d4b",
        "689394ef7ba62b237b236d4a",
        "689394ef7ba62b237b236d4c",
        "689394ef7ba62b237b236d51",
        "689394ef7ba62b237b236d59",
        "689394ef7ba62b237b236d63",
        "689394ef7ba62b237b236d7d"
    ]
    
    await check_multiple_documents(object_ids)

if __name__ == "__main__":
    asyncio.run(main()) 
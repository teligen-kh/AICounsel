#!/usr/bin/env python3
"""
특정 ObjectID의 문서를 확인하는 스크립트
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

async def check_document_by_id(object_id_str: str):
    """특정 ObjectID의 문서를 확인합니다."""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # ObjectID 변환
        object_id = ObjectId(object_id_str)
        logger.info(f"확인할 ObjectID: {object_id}")
        
        # 모든 컬렉션에서 해당 문서 찾기
        collections = [
            'knowledge_base',
            'context_patterns', 
            'input_keywords',
            'conversations',
            'context_rules'
        ]
        
        found = False
        for collection_name in collections:
            collection = getattr(db, collection_name)
            
            # 해당 ObjectID로 문서 검색
            document = await collection.find_one({"_id": object_id})
            
            if document:
                found = True
                logger.info(f"✅ 문서를 찾았습니다! 컬렉션: {collection_name}")
                logger.info("=" * 50)
                logger.info(f"문서 내용:")
                
                # 문서 내용 출력
                for key, value in document.items():
                    if key == "_id":
                        logger.info(f"  {key}: {value}")
                    elif isinstance(value, str) and len(value) > 100:
                        logger.info(f"  {key}: {value[:100]}...")
                    else:
                        logger.info(f"  {key}: {value}")
                
                logger.info("=" * 50)
                break
        
        if not found:
            logger.warning(f"❌ ObjectID {object_id}를 가진 문서를 찾을 수 없습니다.")
            logger.info("모든 컬렉션에서 검색했지만 해당 문서가 존재하지 않습니다.")
            
    except Exception as e:
        logger.error(f"문서 확인 중 오류: {e}")

async def main():
    """메인 함수"""
    object_id = "689394ef7ba62b237b236cdf"
    await check_document_by_id(object_id)

if __name__ == "__main__":
    asyncio.run(main()) 
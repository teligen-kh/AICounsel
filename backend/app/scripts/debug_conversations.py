"""
conversations 테이블 디버그 스크립트
테이블 구조와 데이터를 확인
"""

import asyncio
import motor.motor_asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_conversations():
    """conversations 테이블 디버그"""
    
    # MongoDB 연결
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        logger.info("=== conversations 테이블 디버그 시작 ===")
        
        # 1. 테이블 존재 확인
        collections = await db.list_collection_names()
        logger.info(f"전체 컬렉션: {collections}")
        
        if "conversations" not in collections:
            logger.error("❌ conversations 컬렉션이 존재하지 않습니다!")
            return
        
        # 2. 데이터 개수 확인
        count = await db.conversations.count_documents({})
        logger.info(f"conversations 데이터 개수: {count}")
        
        if count == 0:
            logger.error("❌ conversations 테이블이 비어있습니다!")
            return
        
        # 3. 첫 번째 문서 구조 확인
        first_doc = await db.conversations.find_one({})
        if first_doc:
            logger.info(f"첫 번째 문서 구조:")
            for key, value in first_doc.items():
                logger.info(f"  {key}: {type(value).__name__} = {str(value)[:100]}...")
        
        # 4. 컬럼명 확인
        sample_docs = []
        async for doc in db.conversations.find({}).limit(5):
            sample_docs.append(doc)
        
        logger.info(f"\n샘플 문서들:")
        for i, doc in enumerate(sample_docs):
            logger.info(f"\n문서 {i+1}:")
            for key, value in doc.items():
                logger.info(f"  {key}: {str(value)[:100]}...")
        
        # 5. 요청내용 컬럼 확인
        if "요청내용" in first_doc:
            logger.info(f"\n✅ '요청내용' 컬럼이 존재합니다!")
            
            # 요청내용이 있는 문서들 확인
            request_docs = []
            async for doc in db.conversations.find({"요청내용": {"$exists": True, "$ne": ""}}).limit(10):
                request_docs.append(doc)
            
            logger.info(f"요청내용이 있는 문서 수: {len(request_docs)}")
            
            for i, doc in enumerate(request_docs):
                request_content = doc.get("요청내용", "")
                logger.info(f"  {i+1}. {request_content}")
        
        else:
            logger.error("❌ '요청내용' 컬럼이 존재하지 않습니다!")
            
            # 다른 가능한 컬럼명들 확인
            possible_columns = ["question", "request", "message", "content", "text", "input"]
            for col in possible_columns:
                if col in first_doc:
                    logger.info(f"  발견된 컬럼: {col}")
        
        # 6. 데이터 타입 확인
        logger.info(f"\n데이터 타입 분석:")
        field_types = {}
        async for doc in db.conversations.find({}).limit(100):
            for key, value in doc.items():
                if key not in field_types:
                    field_types[key] = set()
                field_types[key].add(type(value).__name__)
        
        for field, types in field_types.items():
            logger.info(f"  {field}: {list(types)}")
        
    except Exception as e:
        logger.error(f"디버그 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_conversations()) 
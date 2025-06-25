#!/usr/bin/env python3
"""
검색 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.services.mongodb_search_service import MongoDBSearchService
from app.core.database import connect_to_mongo, close_mongo_connection

async def debug_search():
    """검색 과정 디버깅"""
    print("=" * 60)
    print("검색 디버깅")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        await connect_to_mongo()
        print("데이터베이스 연결 성공")
        
        # 검색 서비스 초기화
        from app.core.database import Database
        from app.config import settings
        db = Database.client[settings.DB_NAME]
        service = MongoDBSearchService(db)
        
        # 테스트 쿼리
        query = "DB 늘리기 방법"
        print(f"검색 쿼리: {query}")
        
        # 1. 키워드 추출
        keywords = service._extract_keywords(query)
        print(f"추출된 키워드: {keywords}")
        
        # 2. 정확한 매치 검색
        print("\n=== 정확한 매치 검색 ===")
        exact_match = await service._search_exact_match(query)
        print(f"정확한 매치 결과: {exact_match}")
        
        # 3. 키워드 기반 검색
        print("\n=== 키워드 기반 검색 ===")
        keyword_match = await service._search_by_keywords(keywords)
        print(f"키워드 매치 결과: {keyword_match}")
        
        # 4. 직접 DB 검색 테스트
        print("\n=== 직접 DB 검색 테스트 ===")
        db_related = await db.knowledge_base.find({
            "$or": [
                {"question": {"$regex": "DB", "$options": "i"}},
                {"question": {"$regex": "늘리", "$options": "i"}},
                {"answer": {"$regex": "DB", "$options": "i"}},
                {"answer": {"$regex": "늘리", "$options": "i"}}
            ]
        }).to_list(None)
        
        print(f"직접 검색 결과 수: {len(db_related)}")
        for i, doc in enumerate(db_related[:3], 1):
            print(f"\n결과 {i}:")
            print(f"질문: {doc.get('question', 'N/A')}")
            print(f"답변: {doc.get('answer', 'N/A')[:100]}...")
            
    except Exception as e:
        print(f"오류: {str(e)}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(debug_search()) 
#!/usr/bin/env python3
"""
DB 검색 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.services.llm_service import LLMService
from app.core.database import connect_to_mongo, close_mongo_connection

async def test_db_search():
    """DB 검색 테스트"""
    print("=" * 60)
    print("DB 검색 테스트")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        await connect_to_mongo()
        print("데이터베이스 연결 성공")
        
        # LLM 서비스 초기화 (DB 우선 모드)
        service = LLMService(use_db_priority=True)
        print("LLM 서비스 초기화 완료")
        
        # 테스트 쿼리들
        test_queries = [
            "DB 늘리기 방법",
            "데이터베이스 공간 늘리는 방법",
            "ARUMLOCADB TABLE 늘리기"
        ]
        
        for query in test_queries:
            print(f"\n질문: {query}")
            result = await service.process_message(query)
            print(f"응답: {repr(result)}")
            print("-" * 40)
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_db_search()) 
#!/usr/bin/env python3
"""
DB 데이터 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.core.database import connect_to_mongo, close_mongo_connection
from app.config import settings

async def check_db_data():
    """DB 데이터 확인"""
    print("=" * 60)
    print("DB 데이터 확인")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        await connect_to_mongo()
        print("데이터베이스 연결 성공")
        
        from app.core.database import Database
        db = Database.client[settings.DB_NAME]
        
        # knowledge_base 컬렉션 확인
        knowledge_count = await db.knowledge_base.count_documents({})
        print(f"knowledge_base 문서 수: {knowledge_count}")
        
        if knowledge_count > 0:
            print("\n=== knowledge_base 샘플 데이터 ===")
            sample_data = await db.knowledge_base.find({}).limit(3).to_list(3)
            for i, doc in enumerate(sample_data, 1):
                print(f"\n문서 {i}:")
                print(f"질문: {doc.get('question', 'N/A')}")
                print(f"답변: {doc.get('answer', 'N/A')[:100]}...")
                print(f"키워드: {doc.get('keywords', [])}")
        
        # conversations 컬렉션 확인
        conv_count = await db.conversations.count_documents({})
        print(f"\nconversations 문서 수: {conv_count}")
        
        if conv_count > 0:
            print("\n=== conversations 샘플 데이터 ===")
            sample_conv = await db.conversations.find({}).limit(1).to_list(1)
            if sample_conv:
                doc = sample_conv[0]
                print(f"사용자 메시지: {doc.get('user_message', 'N/A')}")
                print(f"어시스턴트 메시지: {doc.get('assistant_message', 'N/A')[:100]}...")
        
        # DB 관련 데이터 검색
        print("\n=== DB 관련 데이터 검색 ===")
        db_related = await db.knowledge_base.find({
            "$or": [
                {"question": {"$regex": "DB", "$options": "i"}},
                {"question": {"$regex": "데이터베이스", "$options": "i"}},
                {"question": {"$regex": "늘리", "$options": "i"}},
                {"answer": {"$regex": "DB", "$options": "i"}},
                {"answer": {"$regex": "데이터베이스", "$options": "i"}},
                {"answer": {"$regex": "늘리", "$options": "i"}}
            ]
        }).to_list(None)
        
        print(f"DB 관련 데이터 수: {len(db_related)}")
        for i, doc in enumerate(db_related, 1):
            print(f"\nDB 관련 데이터 {i}:")
            print(f"질문: {doc.get('question', 'N/A')}")
            print(f"답변: {doc.get('answer', 'N/A')[:100]}...")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check_db_data()) 
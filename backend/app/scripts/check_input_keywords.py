#!/usr/bin/env python3
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database

async def check_input_keywords():
    db = await get_database()
    
    # 전체 키워드 개수 확인
    total_count = await db.input_keywords.count_documents({})
    print(f"input_keywords 테이블 총 개수: {total_count}")
    
    if total_count == 0:
        print("input_keywords 테이블이 비어있습니다.")
        return
    
    # 첫 번째 문서의 구조 확인
    first_doc = await db.input_keywords.find_one({})
    print(f"\n첫 번째 문서 구조:")
    for key, value in first_doc.items():
        print(f"- {key}: {value}")
    
    # 모든 키워드 조회 (상위 10개)
    all_keywords = await db.input_keywords.find({}).limit(10).to_list(length=10)
    
    print(f"\n전체 키워드들 (상위 10개):")
    for kw in all_keywords:
        print(f"- {kw}")

if __name__ == "__main__":
    asyncio.run(check_input_keywords()) 
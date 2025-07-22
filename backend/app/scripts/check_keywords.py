"""
input_keywords 테이블 확인 스크립트
현재 등록된 키워드들을 확인
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_keywords():
    """input_keywords 테이블 확인"""
    
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client['aicounsel']
    keyword_collection = db.input_keywords
    
    try:
        print("=" * 60)
        print("input_keywords 테이블 확인")
        print("=" * 60)
        
        # 모든 카테고리 조회
        async for category in keyword_collection.find({}):
            print(f"\n📁 카테고리: {category['category']}")
            print(f"📝 설명: {category.get('description', '설명 없음')}")
            print(f"🔢 키워드 수: {len(category['keywords'])}")
            print(f"📅 생성일: {category.get('created_at', '날짜 없음')}")
            print(f"📅 수정일: {category.get('updated_at', '날짜 없음')}")
            
            # 키워드 목록 (처음 20개만)
            print("🔑 키워드 목록:")
            for i, keyword in enumerate(category['keywords'][:20], 1):
                print(f"  {i:2d}. {keyword}")
            
            if len(category['keywords']) > 20:
                print(f"  ... 외 {len(category['keywords']) - 20}개")
            
            print("-" * 40)
        
        print("=" * 60)
        print("확인 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_keywords()) 
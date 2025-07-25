import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def remove_duplicate_견적서():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        print("🧹 중복 견적서 질문 정리")
        print("=" * 50)
        
        # 견적서 관련 질문들 찾기
        results = await db.knowledge_base.find({
            'question': {'$regex': '견적서.*참조사항', '$options': 'i'}
        }).to_list(length=None)
        
        print(f"견적서 참조사항 관련 질문: {len(results)}개")
        
        if len(results) > 1:
            print("\n중복 발견! 정리 중...")
            
            # 첫 번째는 유지하고 나머지는 삭제
            for i, result in enumerate(results[1:], 1):
                print(f"삭제: {result['question']}")
                await db.knowledge_base.delete_one({'_id': result['_id']})
            
            print(f"✅ {len(results)-1}개 중복 제거 완료")
        else:
            print("✅ 중복 없음")
        
        # 정리 후 확인
        remaining = await db.knowledge_base.find({
            'question': {'$regex': '견적서.*참조사항', '$options': 'i'}
        }).to_list(length=None)
        
        print(f"\n정리 후 견적서 참조사항 질문: {len(remaining)}개")
        for i, result in enumerate(remaining, 1):
            print(f"  {i}. {result['question']}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(remove_duplicate_견적서()) 
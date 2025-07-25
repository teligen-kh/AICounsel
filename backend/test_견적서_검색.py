import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_견적서_검색():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        print("🔍 견적서 관련 DB 검색 테스트")
        print("=" * 50)
        
        # 1. 견적서 관련 질문 검색
        print("\n1. '견적서' 키워드로 검색:")
        results = await db.knowledge_base.find({
            'question': {'$regex': '견적서', '$options': 'i'}
        }).to_list(length=5)
        
        print(f"견적서 관련 질문: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Q: {result['question']}")
            print(f"     A: {result['answer'][:100]}...")
        
        # 2. 참조사항 관련 검색
        print("\n2. '참조사항' 키워드로 검색:")
        results = await db.knowledge_base.find({
            'question': {'$regex': '참조사항', '$options': 'i'}
        }).to_list(length=5)
        
        print(f"참조사항 관련 질문: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Q: {result['question']}")
            print(f"     A: {result['answer'][:100]}...")
        
        # 3. 전체 DB 개수 확인
        total_count = await db.knowledge_base.count_documents({})
        print(f"\n3. 전체 knowledge_base 개수: {total_count}개")
        
        # 4. 샘플 데이터 확인
        print("\n4. 샘플 데이터 (최근 3개):")
        sample_results = await db.knowledge_base.find({}).sort('_id', -1).limit(3).to_list(length=3)
        for i, result in enumerate(sample_results, 1):
            print(f"  {i}. Q: {result['question']}")
            print(f"     A: {result['answer'][:100]}...")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_견적서_검색()) 
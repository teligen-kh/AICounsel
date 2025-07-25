import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_exact_match():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        print("🔍 정확한 매치 테스트")
        print("=" * 50)
        
        # 1. knowledge_base에서 실제 질문 가져오기
        print("\n1. knowledge_base에서 실제 질문들:")
        questions = await db.knowledge_base.find({}).limit(5).to_list(length=5)
        
        for i, item in enumerate(questions, 1):
            question = item['question']
            print(f"  {i}. {question}")
            
            # 2. 이 질문으로 정확한 검색 테스트
            print(f"     → 검색 결과:")
            
            # 정확한 매치
            exact_result = await db.knowledge_base.find_one({
                "question": {"$regex": f"^{question}$", "$options": "i"}
            })
            if exact_result:
                print(f"       ✅ 정확한 매치: {exact_result['answer'][:50]}...")
            else:
                print(f"       ❌ 정확한 매치 실패")
            
            # 부분 매치
            partial_result = await db.knowledge_base.find_one({
                "question": {"$regex": question, "$options": "i"}
            })
            if partial_result:
                print(f"       ✅ 부분 매치: {partial_result['answer'][:50]}...")
            else:
                print(f"       ❌ 부분 매치 실패")
            
            print()
        
        # 3. 특정 질문으로 테스트
        test_question = "견적서 출력하면 참조사항이라고 있던데 이건 어디에 넣은 정보가 출력되는건가요?"
        print(f"\n2. 특정 질문 테스트: {test_question}")
        
        # 정확한 매치
        exact_result = await db.knowledge_base.find_one({
            "question": {"$regex": f"^{test_question}$", "$options": "i"}
        })
        if exact_result:
            print(f"✅ 정확한 매치 성공: {exact_result['answer'][:100]}...")
        else:
            print(f"❌ 정확한 매치 실패")
            
            # 실제 DB에 있는지 확인
            all_results = await db.knowledge_base.find({
                "question": {"$regex": "견적서.*참조사항", "$options": "i"}
            }).to_list(length=None)
            print(f"   관련 질문 {len(all_results)}개 발견:")
            for result in all_results:
                print(f"   - {result['question']}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_exact_match()) 
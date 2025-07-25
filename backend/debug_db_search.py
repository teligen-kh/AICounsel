import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_search_service import MongoDBSearchService

async def debug_db_search():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        search_service = MongoDBSearchService(db)
        
        # 테스트 질문
        test_questions = [
            "포스에서 판매시 고객에서 포인트적립을 해주고 싶은데 설정방법이 궁금해요",
            "견적서 출력하면 참조사항이라고 있던데 이건 어디에 넣은 정보가 출력되는건가요?",
            "포인트 적립 방법",
            "포인트 설정"
        ]
        
        for question in test_questions:
            print(f"\n🔍 테스트 질문: {question}")
            print("=" * 60)
            
            # 1. 키워드 추출 테스트
            keywords = search_service._extract_keywords(question)
            print(f"추출된 키워드: {keywords}")
            
            # 2. 정확한 매치 검색 테스트
            print("\n1. 정확한 매치 검색:")
            exact_match = await search_service._search_exact_match(question)
            if exact_match:
                print(f"✅ 찾음: {exact_match[:100]}...")
            else:
                print("❌ 찾지 못함")
            
            # 3. 키워드 기반 검색 테스트
            print("\n2. 키워드 기반 검색:")
            keyword_match = await search_service._search_by_keywords(keywords)
            if keyword_match:
                print(f"✅ 찾음: {keyword_match[:100]}...")
            else:
                print("❌ 찾지 못함")
            
            # 4. 전체 검색 테스트
            print("\n3. 전체 검색:")
            full_result = await search_service.search_answer(question)
            if full_result:
                print(f"✅ 찾음: {full_result[:100]}...")
            else:
                print("❌ 찾지 못함")
            
            print("-" * 60)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_db_search()) 
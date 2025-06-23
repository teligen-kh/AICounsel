import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_search_service import MongoDBSearchService

async def debug_search():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        search_service = MongoDBSearchService(db)
        
        # 문제가 되는 질문들
        test_questions = [
            "코드 있어요. 설치방법 알려주세요",
            "6버전 클라우드 설치",
            "포스 재설치 방법"
        ]
        
        for question in test_questions:
            print(f'\n=== 질문: {question} ===')
            print('-' * 50)
            
            # 키워드 추출 확인
            keywords = search_service._extract_improved_keywords(question)
            print(f'추출된 키워드: {keywords}')
            
            # 모든 지식 베이스 항목에서 점수 계산
            all_items = await db.knowledge_base.find({}).to_list(length=None)
            
            scored_results = []
            for item in all_items:
                score = search_service._calculate_relevance_score(item, keywords)
                if score > 0:
                    scored_results.append((score, item))
            
            # 점수순으로 정렬
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            print(f'\n상위 5개 결과:')
            for i, (score, item) in enumerate(scored_results[:5], 1):
                print(f'{i}. (점수: {score:.2f})')
                print(f'   Q: {item["question"]}')
                print(f'   A: {item["answer"][:100]}...')
                print()
            
            print('=' * 60)
            
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_search()) 
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_search_service import MongoDBSearchService

async def test_improved_service():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        # 검색 서비스 초기화
        search_service = MongoDBSearchService(db)
        
        # 테스트 질문들
        test_questions = [
            "포스 재설치 어떻게 해요?",
            "키오스크 터치가 안돼요",
            "프린터 오류가 발생했어요",
            "백업은 어떻게 하나요?",
            "SQL 설치 오류",
            "프로그램이 실행되지 않아요"
        ]
        
        for question in test_questions:
            print(f'\n질문: {question}')
            print('-' * 50)
            
            # 개선된 검색 서비스 사용
            results = await search_service.search_relevant_answers(question, limit=3)
            
            if results:
                print(f'검색 결과: {len(results)}개')
                for i, result in enumerate(results, 1):
                    print(f'{i}. (점수: {result["score"]:.2f}, 타입: {result.get("match_type", "unknown")})')
                    print(f'   Q: {result.get("question", "N/A")}')
                    answer_preview = result["content"][:150] + "..." if len(result["content"]) > 150 else result["content"]
                    print(f'   A: {answer_preview}')
                    print()
            else:
                print('검색 결과 없음')
            
            print('=' * 60)
            
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_improved_service()) 
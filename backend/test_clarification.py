import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_search_service import MongoDBSearchService

async def test_clarification():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        search_service = MongoDBSearchService(db)
        
        # 테스트 질문들
        test_questions = [
            "코드 있어요. 설치방법 알려주세요",
            "설치하고 싶어요",
            "오류가 발생했어요",
            "문제가 있어요",
            "도움이 필요해요",
            "포스 재설치 방법",
            "키오스크 터치가 안돼요"
        ]
        
        for question in test_questions:
            print(f'\n질문: {question}')
            print('-' * 50)
            
            # 최고 답변 가져오기
            best_answer = await search_service.get_best_answer(question)
            
            if best_answer:
                print(f'답변: {best_answer}')
            else:
                print('답변 없음')
            
            print('=' * 60)
            
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_clarification()) 
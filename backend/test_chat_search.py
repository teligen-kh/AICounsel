import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import re

async def test_chat_search():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
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
            
            # 키워드 추출 (간단한 방식)
            keywords = []
            for word in question.split():
                if len(word) > 1:  # 1글자 제외
                    keywords.append(word)
            
            # MongoDB에서 검색
            search_query = {
                '$or': [
                    {'question': {'$regex': '|'.join(keywords), '$options': 'i'}},
                    {'answer': {'$regex': '|'.join(keywords), '$options': 'i'}}
                ]
            }
            
            results = await db.knowledge_base.find(search_query).limit(3).to_list(length=3)
            
            if results:
                print(f'검색 결과: {len(results)}개')
                for i, result in enumerate(results, 1):
                    print(f'{i}. Q: {result["question"]}')
                    answer_preview = result["answer"][:100] + "..." if len(result["answer"]) > 100 else result["answer"]
                    print(f'   A: {answer_preview}')
                    print()
            else:
                print('검색 결과 없음')
            
            print('=' * 60)
            
    except Exception as e:
        print(f'오류 발생: {e}')
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_chat_search()) 
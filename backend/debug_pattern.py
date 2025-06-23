import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_search_service import MongoDBSearchService

async def debug_pattern():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        search_service = MongoDBSearchService(db)
        
        # 테스트 질문들
        test_questions = [
            "포스 재설치 방법",
            "키오스크 터치가 안돼요",
            "설치하고 싶어요",
            "오류가 발생했어요"
        ]
        
        for question in test_questions:
            print(f'\n=== 질문: {question} ===')
            print('-' * 50)
            
            # 키워드 추출
            keywords = search_service._extract_improved_keywords(question)
            print(f'추출된 키워드: {keywords}')
            
            # 일반적인 질문인지 확인
            is_general = search_service._is_too_general(question)
            print(f'일반적인 질문인가? {is_general}')
            
            # 구체적인 패턴 매칭 확인
            query_lower = question.lower().strip()
            specific_patterns = [
                '포스 재설치',
                '포스 설치',
                '키오스크 터치',
                '프린터 오류',
                '백업 방법',
                'sql 설치',
                '클라우드 설치',
                '6버전 설치',
                '프로그램 실행',
                '연결 문제',
                '설정 방법'
            ]
            
            print('구체적인 패턴 매칭:')
            for pattern in specific_patterns:
                if pattern in query_lower:
                    print(f'  ✓ "{pattern}" 매칭됨')
                else:
                    print(f'  ✗ "{pattern}" 매칭 안됨')
            
            print('=' * 60)
            
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_pattern()) 
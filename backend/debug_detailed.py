import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.mongodb_search_service import MongoDBSearchService

async def debug_detailed():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        search_service = MongoDBSearchService(db)
        
        # 테스트 질문
        question = "포스 재설치 방법"
        
        print(f'=== 질문: {question} ===')
        print('-' * 50)
        
        # 1. 길이 확인
        length = len(question.strip())
        print(f'1. 길이 확인: {length}글자 (10글자 이상? {length >= 10})')
        
        # 2. 구체적인 패턴 확인
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
        
        print('2. 구체적인 패턴 확인:')
        specific_found = False
        for pattern in specific_patterns:
            if pattern in query_lower:
                print(f'  ✓ "{pattern}" 매칭됨')
                specific_found = True
                break
        if not specific_found:
            print('  ✗ 구체적인 패턴 없음')
        
        # 3. 일반적인 패턴 확인
        general_patterns = [
            '설치하고 싶어요',
            '설치하고 싶습니다',
            '설치해주세요',
            '오류가 발생했어요',
            '오류가 발생했습니다',
            '문제가 있어요',
            '문제가 있습니다',
            '도움이 필요해요',
            '도움이 필요합니다',
            '어떻게 하나요',
            '어떻게 하나요?',
            '어떻게 해요',
            '어떻게 해요?',
            '알려주세요',
            '알려주세요.',
            '알려주세요?'
        ]
        
        print('3. 일반적인 패턴 확인:')
        general_found = False
        for pattern in general_patterns:
            if pattern in query_lower:
                print(f'  ✓ "{pattern}" 매칭됨')
                general_found = True
                break
        if not general_found:
            print('  ✗ 일반적인 패턴 없음')
        
        # 4. 키워드 개수 확인
        keywords = search_service._extract_improved_keywords(question)
        print(f'4. 키워드 개수: {len(keywords)}개 ({keywords})')
        
        # 5. 최종 결과
        is_general = search_service._is_too_general(question)
        print(f'5. 최종 결과: 일반적인 질문인가? {is_general}')
        
        print('=' * 60)
        
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_detailed()) 
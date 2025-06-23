import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import re
from collections import Counter

async def improved_search():
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
            
            # 1단계: 정확한 키워드 매칭
            exact_matches = await db.knowledge_base.find({
                'question': {'$regex': question.replace(' ', '.*'), '$options': 'i'}
            }).limit(5).to_list(length=5)
            
            if exact_matches:
                print(f'정확한 매칭 결과: {len(exact_matches)}개')
                for i, result in enumerate(exact_matches, 1):
                    print(f'{i}. Q: {result["question"]}')
                    answer_preview = result["answer"][:100] + "..." if len(result["answer"]) > 100 else result["answer"]
                    print(f'   A: {answer_preview}')
                    print()
            else:
                print('정확한 매칭 결과 없음')
                
                # 2단계: 키워드 기반 검색
                keywords = extract_keywords(question)
                print(f'추출된 키워드: {keywords}')
                
                # 키워드별 점수 계산
                scored_results = []
                all_results = await db.knowledge_base.find({}).to_list(length=None)
                
                for result in all_results:
                    score = calculate_relevance_score(result, keywords)
                    if score > 0:
                        scored_results.append((score, result))
                
                # 점수순으로 정렬
                scored_results.sort(key=lambda x: x[0], reverse=True)
                
                print(f'키워드 기반 검색 결과: {len(scored_results[:3])}개')
                for i, (score, result) in enumerate(scored_results[:3], 1):
                    print(f'{i}. (점수: {score:.2f}) Q: {result["question"]}')
                    answer_preview = result["answer"][:100] + "..." if len(result["answer"]) > 100 else result["answer"]
                    print(f'   A: {answer_preview}')
                    print()
            
            print('=' * 60)
            
    except Exception as e:
        print(f'오류 발생: {e}')
    finally:
        client.close()

def extract_keywords(text):
    """텍스트에서 의미있는 키워드 추출"""
    # 불용어 제거
    stop_words = {'어떻게', '해요', '돼요', '있어요', '하나요', '오류', '발생', '했어요', '안돼요'}
    
    # 특수문자 제거 및 소문자 변환
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    
    # 불용어 제거 및 2글자 이상만 선택
    keywords = [word for word in words if word not in stop_words and len(word) >= 2]
    
    return keywords

def calculate_relevance_score(result, keywords):
    """검색 결과와 키워드 간의 관련성 점수 계산"""
    score = 0
    question = result['question'].lower()
    answer = result['answer'].lower()
    
    for keyword in keywords:
        # 질문에 키워드가 있으면 높은 점수
        if keyword in question:
            score += 3
        # 답변에 키워드가 있으면 중간 점수
        if keyword in answer:
            score += 1
    
    return score

if __name__ == "__main__":
    asyncio.run(improved_search()) 
import pandas as pd
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
from pathlib import Path

def extract_keywords(text: str) -> list:
    """텍스트에서 키워드를 추출합니다."""
    if not text or pd.isna(text):
        return []
    
    # 한국어 조사, 접속사 등 제거
    stop_words = ['이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', '은', '는', '이', '그', '저', '어떤', '무엇', '어떻게', '왜', '언제', '어디서', '안', '되', '됨', '요', '다', '니다', '습니다']
    
    # 특수문자 제거 및 소문자 변환
    cleaned_text = re.sub(r'[^\w\s가-힣]', ' ', str(text).lower())
    
    # 단어 분리
    words = cleaned_text.split()
    
    # 불용어 제거 및 2글자 이상 단어만 선택
    keywords = [word for word in words if word not in stop_words and len(word) >= 2]
    
    return keywords

def categorize_problem(question: str) -> str:
    """문제를 카테고리로 분류합니다."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['카드', '결제', '리더기', '단말기']):
        return "결제"
    elif any(word in question_lower for word in ['상품', '검색', '바코드', '알파넷']):
        return "상품관리"
    elif any(word in question_lower for word in ['포스', '설치', '재설치', '백업']):
        return "시스템설치"
    elif any(word in question_lower for word in ['프린터', '출력', '인쇄']):
        return "하드웨어"
    elif any(word in question_lower for word in ['키오스크', '터치']):
        return "키오스크"
    elif any(word in question_lower for word in ['네트워크', '연결', '인터넷']):
        return "네트워크"
    elif any(word in question_lower for word in ['로그인', '인증', '비밀번호']):
        return "인증"
    else:
        return "기타"

async def import_counseling_data():
    """상담 학습 데이터를 MongoDB 지식 베이스로 변환합니다."""
    
    # CSV 파일 경로
    csv_path = Path("D:/AICounsel/data/csv/Counseling Training Data.csv")
    
    if not csv_path.exists():
        print(f"CSV 파일이 존재하지 않습니다: {csv_path}")
        return
    
    # CSV 파일 읽기
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"CSV 파일 읽기 성공: {len(df)}행")
    except Exception as e:
        print(f"CSV 파일 읽기 오류: {str(e)}")
        return
    
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client['aicounsel']
    knowledge_collection = db.knowledge_base
    
    # 기존 지식 베이스 데이터 삭제 (선택사항)
    # await knowledge_collection.delete_many({})
    # print("기존 지식 베이스 데이터를 삭제했습니다.")
    
    # 데이터 변환 및 저장
    imported_count = 0
    skipped_count = 0
    
    for index, row in df.iterrows():
        try:
            question = str(row['요청내용']).strip()
            answer = str(row['처리내용 표준화']).strip()
            
            # 빈 데이터 건너뛰기
            if not question or not answer or question == 'nan' or answer == 'nan':
                skipped_count += 1
                continue
            
            # 키워드 추출
            keywords = extract_keywords(question)
            
            # 카테고리 분류
            category = categorize_problem(question)
            
            # 지식 베이스 항목 생성
            knowledge_item = {
                'question': question,
                'answer': answer,
                'keywords': keywords,
                'category': category,
                'source': 'counseling_data',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # 중복 확인 (동일한 질문이 있는지)
            existing = await knowledge_collection.find_one({"question": question})
            if existing:
                print(f"중복 항목 건너뛰기: {question[:50]}...")
                skipped_count += 1
                continue
            
            # MongoDB에 저장
            await knowledge_collection.insert_one(knowledge_item)
            imported_count += 1
            
            if imported_count % 50 == 0:
                print(f"진행률: {imported_count}/{len(df)}")
                
        except Exception as e:
            print(f"행 {index} 처리 오류: {str(e)}")
            skipped_count += 1
    
    # 결과 출력
    total_count = await knowledge_collection.count_documents({})
    print(f"\n=== 변환 완료 ===")
    print(f"새로 추가된 항목: {imported_count}개")
    print(f"건너뛴 항목: {skipped_count}개")
    print(f"총 지식 베이스 항목: {total_count}개")
    
    # 카테고리별 통계
    print(f"\n=== 카테고리별 통계 ===")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    async for result in knowledge_collection.aggregate(pipeline):
        print(f"{result['_id']}: {result['count']}개")
    
    client.close()
    print("\n상담 데이터 변환이 완료되었습니다.")

if __name__ == "__main__":
    asyncio.run(import_counseling_data()) 
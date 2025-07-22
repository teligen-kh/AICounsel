"""
키워드 테이블 생성 스크립트
입력 분류를 위한 키워드를 DB에서 관리하도록 설정
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def create_keyword_table():
    """키워드 테이블을 생성하고 초기 데이터를 추가합니다."""
    
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client['aicounsel']
    
    # 키워드 테이블 컬렉션
    keyword_collection = db.input_keywords
    
    # 기존 데이터 삭제
    await keyword_collection.delete_many({})
    print("기존 키워드 테이블 데이터를 삭제했습니다.")
    
    # 키워드 데이터 정의
    keyword_data = [
        # 일상 대화 키워드 (인사말 포함)
        {
            "category": "casual",
            "keywords": ["안녕하세요", "안녕", "반갑습니다", "반가워요", "좋은 아침", "좋은 오후", "좋은 저녁", "하이", "hi", "hello", "바쁘시죠", "식사", "점심", "저녁", "아침", "커피", "차", "날씨", "기분", "피곤", "힘드시", "어떻게 지내", "잘 지내", "너는", "당신은", "ai", "인공지능", "로봇", "고마워", "감사", "고맙습니다"],
            "description": "일상적인 대화, 인사말, AI 관련 질문",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        
        # 기술적 질문 키워드 (DB에서 자동 추출)
        {
            "category": "technical",
            "keywords": ["설치", "설정", "오류", "에러", "문제", "해결", "방법", "프로그램", "소프트웨어", "하드웨어", "기기", "장비", "스캐너", "프린터", "포스", "pos", "시스템", "네트워크", "연결", "인터넷", "데이터", "백업", "복구", "업데이트"],
            "description": "기술적 문제 해결 및 시스템 관련 질문",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        
        # 비상담 질문 키워드
        {
            "category": "non_counseling",
            "keywords": ["한국", "대한민국", "독도", "일본", "중국", "미국", "영국", "역사", "지리", "수도", "인구", "면적", "언어", "문화", "정치", "경제", "사회", "과학", "수학", "물리", "화학", "생물", "천문", "지구", "달", "태양", "별", "우주", "음식", "요리", "레시피", "영화", "드라마", "음악", "노래", "운동", "스포츠", "축구", "야구", "농구", "테니스", "여행", "관광", "호텔", "항공", "기차", "버스", "의학", "병원", "약", "질병", "건강", "다이어트", "작가", "소설", "책", "문학", "시", "시인", "화가", "미술", "연예인", "배우", "가수", "아이돌", "유명인", "스타", "날씨", "기후", "온도", "비", "눈", "바람", "습도", "요즘", "최근", "트렌드", "유행", "인기", "핫", "화제", "뉴스", "신문", "방송", "미디어", "인터넷", "SNS", "학교", "대학", "학생", "선생님", "교육", "공부", "시험", "직업", "회사", "직장", "사장", "부장", "과장", "대리", "취미", "관심사", "좋아하는", "싫어하는", "선호", "취향"],
            "description": "상담 범위를 벗어나는 일반 지식 질문",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        
        # 욕설 키워드
        {
            "category": "profanity",
            "keywords": ["바보", "멍청", "똥", "개", "새끼", "씨발", "병신", "미친", "미쳤", "돌았", "정신", "빡", "빡치", "열받", "짜증", "화나", "열받", "빡돌", "돌았", "미쳤", "fuck", "shit", "damn", "bitch", "ass", "idiot", "stupid"],
            "description": "욕설 및 공격적 표현",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    # 키워드 테이블에 데이터 삽입
    result = await keyword_collection.insert_many(keyword_data)
    print(f"키워드 테이블에 {len(result.inserted_ids)}개의 카테고리를 추가했습니다.")
    
    # 추가된 데이터 확인
    count = await keyword_collection.count_documents({})
    print(f"현재 키워드 테이블 총 카테고리 수: {count}")
    
    # 샘플 데이터 출력
    print("\n추가된 키워드 카테고리:")
    async for item in keyword_collection.find({}):
        print(f"- {item['category']}: {len(item['keywords'])}개 키워드")
    
    # knowledge_base에서 자동으로 키워드 추출하여 technical 카테고리에 추가
    await extract_technical_keywords_from_db(db, keyword_collection)
    
    client.close()

async def extract_technical_keywords_from_db(db, keyword_collection):
    """knowledge_base에서 기술적 키워드를 자동 추출하여 추가합니다."""
    try:
        # knowledge_base의 모든 키워드 수집
        all_keywords = set()
        async for item in db.knowledge_base.find({}):
            if 'keywords' in item and item['keywords']:
                all_keywords.update(item['keywords'])
        
        if all_keywords:
            # 기존 technical 카테고리 업데이트
            technical_keywords = list(all_keywords)
            
            await keyword_collection.update_one(
                {"category": "technical"},
                {"$set": {
                    "keywords": technical_keywords,
                    "updated_at": datetime.now()
                }}
            )
            
            print(f"knowledge_base에서 {len(technical_keywords)}개의 기술적 키워드를 추출하여 추가했습니다.")
            print(f"추출된 키워드: {technical_keywords[:10]}...")  # 처음 10개만 출력
        
    except Exception as e:
        print(f"키워드 추출 중 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_keyword_table()) 
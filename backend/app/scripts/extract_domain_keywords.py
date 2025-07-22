"""
도메인 키워드 추출 스크립트
knowledge_base에서 전문 상담 키워드만 추출하여 input_keywords 테이블에 입력
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
from collections import Counter

async def extract_domain_keywords():
    """knowledge_base에서 전문 상담 키워드만 추출"""
    
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client['aicounsel']
    
    # 컬렉션
    knowledge_collection = db.knowledge_base
    keyword_collection = db.input_keywords
    
    try:
        print("=" * 60)
        print("도메인 키워드 추출 시작")
        print("=" * 60)
        
        # 1. knowledge_base의 모든 키워드 수집
        all_keywords = []
        async for item in knowledge_collection.find({}):
            if 'keywords' in item and item['keywords']:
                all_keywords.extend(item['keywords'])
        
        print(f"수집된 총 키워드 수: {len(all_keywords)}")
        
        # 2. 키워드 빈도 분석
        keyword_freq = Counter(all_keywords)
        print(f"고유 키워드 수: {len(keyword_freq)}")
        
        # 3. 도메인 관련 키워드 필터링
        domain_keywords = filter_domain_keywords(keyword_freq)
        print(f"도메인 키워드 수: {len(domain_keywords)}")
        
        # 4. input_keywords 테이블 업데이트
        await update_input_keywords(keyword_collection, domain_keywords)
        
        print("=" * 60)
        print("도메인 키워드 추출 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        client.close()

def filter_domain_keywords(keyword_freq: Counter) -> list:
    """도메인 관련 키워드만 필터링"""
    
    # 도메인 관련 키워드 정의 (가이드 기반)
    domain_patterns = [
        # 기술적 용어
        r'.*설치.*', r'.*설정.*', r'.*오류.*', r'.*에러.*', r'.*문제.*', r'.*해결.*', r'.*방법.*',
        r'.*프로그램.*', r'.*소프트웨어.*', r'.*하드웨어.*', r'.*기기.*', r'.*장비.*',
        r'.*스캐너.*', r'.*프린터.*', r'.*포스.*', r'.*pos.*', r'.*시스템.*', r'.*네트워크.*',
        r'.*연결.*', r'.*인터넷.*', r'.*데이터.*', r'.*백업.*', r'.*복구.*', r'.*업데이트.*',
        
        # 업무 관련 용어
        r'.*영수증.*', r'.*결제.*', r'.*카드.*', r'.*키오스크.*', r'.*kiosk.*',
        r'.*듀얼모니터.*', r'.*모니터.*', r'.*화면.*', r'.*디스플레이.*',
        r'.*포트.*', r'.*장치관리자.*', r'.*디바이스.*', r'.*device.*',
        r'.*재연결.*', r'.*출력.*', r'.*정상출력.*', r'.*정상작동.*',
        r'.*다운로드.*', r'.*업로드.*', r'.*설치파일.*', r'.*드라이버.*',
        r'.*재부팅.*', r'.*리부팅.*', r'.*부팅.*', r'.*인터페이스.*',
        r'.*ui.*', r'.*ux.*', r'.*사용자.*', r'.*사용법.*', r'.*매뉴얼.*',
        r'.*설명서.*', r'.*가이드.*', r'.*도움말.*', r'.*help.*',
        
        # 거래 관련 용어
        r'.*거래명세서.*', r'.*직인.*', r'.*계좌번호.*', r'.*로그인.*', r'.*단말기.*',
        r'.*클라우드.*', r'.*재설치.*', r'.*설치요구.*', r'.*작동.*', r'.*재시작.*'
    ]
    
    # 도메인 키워드 필터링
    domain_keywords = []
    
    for keyword, freq in keyword_freq.items():
        # 빈도가 2회 이상이거나 도메인 패턴에 매칭되는 키워드 선택
        if freq >= 2 or any(re.match(pattern, keyword, re.IGNORECASE) for pattern in domain_patterns):
            domain_keywords.append(keyword)
    
    # 비도메인 키워드 제외
    exclude_keywords = [
        '고객님', '팀장', '아침', '커피', '감사', '안녕', '반갑', '좋은', '하이', 'hello',
        '바쁘', '식사', '점심', '저녁', '차', '날씨', '기분', '피곤', '힘드시', '지내',
        '너는', '당신은', 'ai', '인공지능', '로봇'
    ]
    
    domain_keywords = [kw for kw in domain_keywords if kw not in exclude_keywords]
    
    return domain_keywords

async def update_input_keywords(keyword_collection, domain_keywords: list):
    """input_keywords 테이블 업데이트"""
    
    try:
        # technical 카테고리가 있는지 확인
        technical_category = await keyword_collection.find_one({"category": "technical"})
        
        if technical_category:
            # 기존 키워드에 새로운 키워드 추가
            await keyword_collection.update_one(
                {"category": "technical"},
                {"$set": {
                    "keywords": domain_keywords,
                    "updated_at": datetime.now()
                }}
            )
            print(f"기존 technical 카테고리 업데이트: {len(domain_keywords)}개 키워드")
        else:
            # 새로운 technical 카테고리 생성
            await keyword_collection.insert_one({
                "category": "technical",
                "keywords": domain_keywords,
                "description": "기술적 문제 해결 및 시스템 관련 질문",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            print(f"새로운 technical 카테고리 생성: {len(domain_keywords)}개 키워드")
        
        # 추출된 키워드 출력
        print("\n추출된 도메인 키워드 (처음 20개):")
        for i, keyword in enumerate(domain_keywords[:20], 1):
            print(f"{i:2d}. {keyword}")
        
        if len(domain_keywords) > 20:
            print(f"... 외 {len(domain_keywords) - 20}개")
        
    except Exception as e:
        print(f"키워드 업데이트 실패: {str(e)}")

if __name__ == "__main__":
    asyncio.run(extract_domain_keywords()) 
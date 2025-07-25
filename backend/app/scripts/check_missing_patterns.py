"""
누락된 패턴 체크 및 추가 스크립트
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MissingPatternChecker:
    """누락된 패턴 체크 및 추가"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.pattern_collection = db.context_patterns
    
    async def check_missing_patterns(self):
        """누락된 패턴 체크"""
        logger.info("누락된 패턴 체크 시작...")
        
        # 테스트 케이스들
        test_cases = [
            "네, 잘지내고 있어요",
            "네, 잘 지내고 있어요",
            "잘 지내고 있어요",
            "잘지내고 있어요",
            "견적서 출력하면 참조사항이라고 있던데",
            "견적서 출력하면 참조사항",
            "견적서 참조사항",
            "참조사항이 뭐야",
            "참조사항이 무엇인가요",
            "프린터가 안 나와요",
            "프린터가 안 나와",
            "프린터 안됨",
            "프린터 고장",
            "포스 시스템 오류",
            "포스 오류",
            "pos 오류",
            "결제 안됨",
            "카드 결제 안됨",
            "영수증 안 나와요",
            "영수증 출력 안됨",
            "바코드 스캔 안됨",
            "스캐너 안됨",
            "설치 방법",
            "설치 안됨",
            "설정 방법",
            "설정 안됨",
            "네트워크 연결 안됨",
            "인터넷 연결 안됨",
            "로그인 안됨",
            "비밀번호 까먹었어요",
            "계정 잠김",
            "데이터 백업",
            "데이터 복구",
            "업데이트 안됨",
            "드라이버 설치",
            "재설치 방법",
            "키오스크 오류",
            "kiosk 오류",
            "단말기 오류",
            "카드리더기 안됨",
            "원격 접속",
            "원격 설정",
            "접속 안됨",
            "권한 없음",
            "보안 설정",
            "비밀번호 변경",
            "계정 생성",
            "사용자 등록",
            "고객 등록",
            "상품 등록",
            "재고 확인",
            "재고 관리",
            "매출 조회",
            "매출 통계",
            "매출 리포트",
            "매출 분석",
            "매출 집계",
            "매출 정산",
            "매출 정리",
            "매출 확인",
            "매출 조회",
            "매출 통계",
            "매출 리포트",
            "매출 분석",
            "매출 집계",
            "매출 정산",
            "매출 정리",
            "매출 확인",
        ]
        
        missing_patterns = []
        
        for test_case in test_cases:
            # 패턴 검색
            existing = await self.pattern_collection.find_one({"pattern": test_case})
            if not existing:
                missing_patterns.append(test_case)
        
        logger.info(f"누락된 패턴 수: {len(missing_patterns)}")
        for pattern in missing_patterns[:10]:  # 처음 10개만 출력
            logger.info(f"  - {pattern}")
        
        return missing_patterns
    
    async def add_missing_patterns(self, missing_patterns):
        """누락된 패턴 추가"""
        logger.info("누락된 패턴 추가 시작...")
        
        added_count = 0
        
        for pattern in missing_patterns:
            # 문맥 분류
            context = self._classify_context(pattern)
            
            # 패턴 추가
            pattern_doc = {
                "pattern": pattern,
                "context": context,
                "original_question": pattern,
                "is_active": True,
                "accuracy": 0.9,
                "usage_count": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "source": "missing_pattern_added"
            }
            
            await self.pattern_collection.insert_one(pattern_doc)
            added_count += 1
        
        logger.info(f"추가된 패턴 수: {added_count}")
        return added_count
    
    def _classify_context(self, text: str) -> str:
        """텍스트 문맥 분류"""
        text_lower = text.lower()
        
        # 기술적 키워드
        technical_keywords = [
            '프린터', '포스', 'pos', '설치', '설정', '오류', '에러', '문제', '해결',
            '프로그램', '소프트웨어', '하드웨어', '기기', '장비', '스캐너',
            '시스템', '네트워크', '연결', '인터넷', '데이터', '백업', '복구',
            '업데이트', '단말기', '카드', '결제', '영수증', '바코드', 'qr코드',
            '드라이버', '재설치', '키오스크', 'kiosk', '카드리더기', '견적서',
            '참조사항', '참고사항', '매출', '재고', '상품', '고객', '사용자',
            '계정', '비밀번호', '로그인', '접속', '원격', '권한', '보안'
        ]
        
        # 일상 대화 키워드
        casual_keywords = [
            '안녕', '반갑', '하이', 'hello', 'hi', '바쁘', '식사', '점심', '저녁',
            '커피', '차', '날씨', '기분', '피곤', '힘드', '어떻게 지내', '잘 지내',
            '너는', '당신은', 'ai', '인공지능', '로봇', '잘지내', '잘 지내',
            '네', '네,', '네.', '네!', '네?', '네~', '네...', '네,,,'
        ]
        
        # 욕설 키워드
        profanity_keywords = [
            '바보', '멍청', '똥', '개', '새끼', '씨발', '병신', '미친', '미쳤',
            '돌았', '정신', '빡', '빡치'
        ]
        
        # 분류
        for keyword in profanity_keywords:
            if keyword in text_lower:
                return 'profanity'
        
        for keyword in casual_keywords:
            if keyword in text_lower:
                return 'casual'
        
        for keyword in technical_keywords:
            if keyword in text_lower:
                return 'technical'
        
        return 'technical'  # 기본값

async def main():
    """메인 함수"""
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        checker = MissingPatternChecker(db)
        
        # 1. 누락된 패턴 체크
        missing_patterns = await checker.check_missing_patterns()
        
        if missing_patterns:
            # 2. 누락된 패턴 추가
            added_count = await checker.add_missing_patterns(missing_patterns)
            
            print(f"\n🎉 누락된 패턴 추가 완료!")
            print(f"   - 추가된 패턴: {added_count}개")
            
            # 3. 최종 통계
            total_patterns = await checker.pattern_collection.count_documents({})
            print(f"   - 총 패턴 수: {total_patterns}개")
        else:
            print("✅ 모든 패턴이 존재합니다!")
        
    except Exception as e:
        logger.error(f"실행 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 
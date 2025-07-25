"""
knowledge_base → context_patterns 빠른 변환 스크립트
LLM 없이 키워드 기반으로 빠르게 처리
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging
from typing import List, Dict, Set
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastContextPatternGenerator:
    """빠른 context_patterns 생성기"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.pattern_collection = db.context_patterns
        
        # 문맥별 키워드 매핑 (확장)
        self.context_keywords = {
            'technical': [
                # 하드웨어
                '프린터', '스캐너', '카드리더기', '키오스크', 'kiosk', '단말기', '장비', '기기',
                # 소프트웨어
                '포스', 'pos', '프로그램', '소프트웨어', '드라이버', '설치', '재설치',
                # 시스템
                '시스템', '네트워크', '연결', '인터넷', '설정', '업데이트',
                # 문제 해결
                '오류', '에러', '문제', '해결', '수정', '고장', '안됨', '안되',
                # 데이터
                '데이터', '백업', '복구', '저장', '삭제', '이동',
                # 결제
                '결제', '카드', '영수증', '바코드', 'qr코드', 'qr', '직인', '도장',
                # 기타 기술
                '원격', '접속', '로그인', '비밀번호', '계정', '권한', '보안'
            ],
            'casual': [
                # 인사말
                '안녕', '반갑', '하이', 'hello', 'hi', '안녕하세요', '반갑습니다',
                # 일상
                '바쁘', '식사', '점심', '저녁', '아침', '커피', '차', '날씨',
                # 감정/상태
                '기분', '피곤', '힘드', '어떻게 지내', '잘 지내', '괜찮',
                # AI 관련
                '너는', '당신은', 'ai', '인공지능', '로봇', '봇', '챗봇'
            ],
            'non_counseling': [
                # 국가/지역
                '한국', '대한민국', '일본', '중국', '미국', '영국', '프랑스',
                # 역사/지리
                '역사', '지리', '수도', '인구', '면적', '언어', '문화',
                # 정치/경제
                '정치', '경제', '사회', '정부', '대통령', '국회',
                # 과학/학문
                '과학', '수학', '물리', '화학', '생물', '천문', '지구',
                # 일반 지식
                '세계', '우주', '자연', '동물', '식물', '음식', '스포츠'
            ],
            'profanity': [
                # 욕설/비속어
                '바보', '멍청', '똥', '개', '새끼', '씨발', '병신', '미친', '미쳤',
                '돌았', '정신', '빡', '빡치', '개새끼', '병신', '미쳤다'
            ]
        }
    
    def _classify_by_keywords(self, question: str) -> str:
        """키워드 기반 문맥 분류"""
        question_lower = question.lower()
        
        # 각 문맥별 키워드 매칭 점수 계산
        scores = {}
        for context, keywords in self.context_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            scores[context] = score
        
        # 가장 높은 점수의 문맥 반환
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                return max(scores, key=scores.get)
        
        return 'technical'  # 기본값 (상담 데이터이므로)
    
    def _generate_variations(self, question: str, context: str) -> List[str]:
        """질문의 다양한 변형 생성"""
        variations = [question]  # 원본 포함
        
        # 기본 변형 패턴
        basic_patterns = [
            # 질문 형태 변형
            lambda q: q.replace('?', '').strip(),
            lambda q: q.replace('?', '요').strip(),
            lambda q: q.replace('?', '인가요').strip(),
            lambda q: q.replace('?', '할까요').strip(),
            lambda q: q.replace('?', '하나요').strip(),
            
            # 존댓말 변형
            lambda q: q.replace('요', '').strip(),
            lambda q: q.replace('요', '다').strip(),
            lambda q: q.replace('니다', '').strip(),
            lambda q: q.replace('니다', '다').strip(),
            
            # 조사 변형
            lambda q: q.replace('가', '이').strip(),
            lambda q: q.replace('이', '가').strip(),
            lambda q: q.replace('를', '을').strip(),
            lambda q: q.replace('을', '를').strip(),
            lambda q: q.replace('에', '에서').strip(),
            lambda q: q.replace('에서', '에').strip(),
            
            # 부정어 변형
            lambda q: q.replace('안', '안').strip(),
            lambda q: q.replace('안', '못').strip(),
            lambda q: q.replace('못', '안').strip(),
        ]
        
        # 기본 변형 적용
        for pattern in basic_patterns:
            try:
                variation = pattern(question)
                if variation != question and len(variation) > 5:
                    variations.append(variation)
            except:
                continue
        
        # 문맥별 특화 변형
        if context == 'technical':
            tech_variations = [
                lambda q: f"{q} 어떻게 해결하나요?",
                lambda q: f"{q} 방법 알려주세요",
                lambda q: f"{q} 설정 방법",
                lambda q: f"{q} 문제 해결",
                lambda q: f"{q} 오류 수정",
                lambda q: f"{q} 고치는 방법",
                lambda q: f"{q} 해결책",
                lambda q: f"{q} 대처법",
            ]
            
            for pattern in tech_variations:
                try:
                    variation = pattern(question)
                    if len(variation) < 100:  # 너무 길지 않게
                        variations.append(variation)
                except:
                    continue
        
        elif context == 'casual':
            casual_variations = [
                lambda q: f"{q} 어떻게 생각해?",
                lambda q: f"{q} 괜찮을까?",
                lambda q: f"{q} 어떠세요?",
                lambda q: f"{q} 어떠신가요?",
            ]
            
            for pattern in casual_variations:
                try:
                    variation = pattern(question)
                    if len(variation) < 80:
                        variations.append(variation)
                except:
                    continue
        
        # 중복 제거 및 길이 제한
        unique_variations = []
        seen = set()
        for variation in variations:
            if variation not in seen and 5 <= len(variation) <= 100:
                unique_variations.append(variation)
                seen.add(variation)
        
        return unique_variations[:8]  # 최대 8개 변형 (빠른 처리)
    
    async def generate_patterns_fast(self) -> Dict:
        """빠른 패턴 생성"""
        logger.info("빠른 context_patterns 생성 시작...")
        
        # 기존 패턴 수 확인
        existing_count = await self.pattern_collection.count_documents({})
        logger.info(f"기존 context_patterns 수: {existing_count}")
        
        # knowledge_base에서 모든 질문 가져오기
        questions = []
        async for doc in self.knowledge_collection.find({}):
            question = doc.get("question", "").strip()
            if question and len(question) > 5:
                questions.append({
                    "question": question,
                    "answer": doc.get("answer", ""),
                    "category": doc.get("category", "technical"),
                    "keywords": doc.get("keywords", [])
                })
        
        logger.info(f"처리할 질문 수: {len(questions)}")
        
        # 문맥별 통계
        context_stats = {'technical': 0, 'casual': 0, 'non_counseling': 0, 'profanity': 0}
        total_patterns = 0
        
        # 각 질문에 대해 패턴 생성
        for i, q_data in enumerate(questions, 1):
            question = q_data["question"]
            
            # 키워드 기반 문맥 분류 (빠름)
            context = self._classify_by_keywords(question)
            context_stats[context] += 1
            
            # 변형 패턴 생성
            variations = self._generate_variations(question, context)
            
            # 패턴 저장
            for variation in variations:
                pattern_doc = {
                    "pattern": variation,
                    "context": context,
                    "original_question": question,
                    "is_active": True,
                    "accuracy": 0.85,  # 키워드 기반이므로 약간 낮음
                    "usage_count": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "source": "knowledge_base_fast_generated"
                }
                
                # 중복 체크 후 저장
                existing = await self.pattern_collection.find_one({"pattern": variation})
                if not existing:
                    await self.pattern_collection.insert_one(pattern_doc)
                    total_patterns += 1
            
            # 진행률 출력 (더 자주)
            if i % 20 == 0:
                logger.info(f"진행률: {i}/{len(questions)} ({i/len(questions)*100:.1f}%) - 생성된 패턴: {total_patterns}개")
        
        # 최종 통계
        final_count = await self.pattern_collection.count_documents({})
        
        result = {
            "original_patterns": existing_count,
            "new_patterns_generated": total_patterns,
            "total_patterns": final_count,
            "context_distribution": context_stats,
            "questions_processed": len(questions)
        }
        
        logger.info("=== 빠른 변환 완료 ===")
        logger.info(f"기존 패턴: {existing_count}개")
        logger.info(f"새로 생성: {total_patterns}개")
        logger.info(f"총 패턴: {final_count}개")
        logger.info("문맥별 분포:")
        for context, count in context_stats.items():
            logger.info(f"  - {context}: {count}개")
        
        return result
    
    async def cleanup_duplicate_patterns(self) -> Dict:
        """중복 패턴 정리"""
        logger.info("중복 패턴 정리 시작...")
        
        # 모든 패턴 가져오기
        patterns = []
        async for doc in self.pattern_collection.find({}):
            patterns.append(doc)
        
        # 중복 패턴 찾기
        seen_patterns = set()
        duplicates = []
        
        for pattern_doc in patterns:
            pattern = pattern_doc["pattern"].strip().lower()
            if pattern in seen_patterns:
                duplicates.append(pattern_doc["_id"])
            else:
                seen_patterns.add(pattern)
        
        # 중복 패턴 삭제
        if duplicates:
            result = await self.pattern_collection.delete_many({"_id": {"$in": duplicates}})
            deleted_count = result.deleted_count
        else:
            deleted_count = 0
        
        final_count = await self.pattern_collection.count_documents({})
        
        logger.info(f"중복 패턴 삭제: {deleted_count}개")
        logger.info(f"최종 패턴 수: {final_count}개")
        
        return {
            "duplicates_removed": deleted_count,
            "final_patterns": final_count
        }

async def main():
    """메인 함수"""
    # MongoDB 연결
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        generator = FastContextPatternGenerator(db)
        
        print("🚀 빠른 context_patterns 생성 시작!")
        print("   - LLM 없이 키워드 기반으로 빠르게 처리")
        print("   - 예상 시간: 1-2분")
        
        # 1. 패턴 생성
        result = await generator.generate_patterns_fast()
        
        # 2. 중복 정리
        cleanup_result = await generator.cleanup_duplicate_patterns()
        
        # 3. 최종 결과 출력
        print(f"\n🎉 빠른 context_patterns 생성 완료!")
        print(f"   - 기존: {result['original_patterns']}개")
        print(f"   - 새로 생성: {result['new_patterns_generated']}개")
        print(f"   - 중복 제거: {cleanup_result['duplicates_removed']}개")
        print(f"   - 최종: {cleanup_result['final_patterns']}개")
        print(f"   - 처리된 질문: {result['questions_processed']}개")
        
        print(f"\n📊 문맥별 분포:")
        for context, count in result['context_distribution'].items():
            print(f"   - {context}: {count}개")
        
    except Exception as e:
        logger.error(f"실행 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 
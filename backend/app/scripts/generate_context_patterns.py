"""
knowledge_base → context_patterns 자동 변환 스크립트
LLM을 사용하여 질문을 문맥별로 분류하고 다양한 패턴 생성
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging
from typing import List, Dict, Set
import re
import random

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextPatternGenerator:
    """knowledge_base → context_patterns 자동 변환"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.pattern_collection = db.context_patterns
        
        # 문맥별 키워드 매핑
        self.context_keywords = {
            'technical': [
                '프린터', '포스', 'pos', '설치', '설정', '오류', '에러', '문제', '해결',
                '프로그램', '소프트웨어', '하드웨어', '기기', '장비', '스캐너',
                '시스템', '네트워크', '연결', '인터넷', '데이터', '백업', '복구',
                '업데이트', '단말기', '카드', '결제', '영수증', '바코드', 'qr코드',
                '드라이버', '재설치', '키오스크', 'kiosk', '카드리더기'
            ],
            'casual': [
                '안녕', '반갑', '하이', 'hello', 'hi', '바쁘', '식사', '점심', '저녁',
                '커피', '차', '날씨', '기분', '피곤', '힘드', '어떻게 지내', '잘 지내',
                '너는', '당신은', 'ai', '인공지능', '로봇'
            ],
            'non_counseling': [
                '한국', '대한민국', '일본', '중국', '미국', '역사', '지리', '수도',
                '인구', '면적', '언어', '문화', '정치', '경제', '사회', '과학',
                '수학', '물리', '화학', '생물'
            ],
            'profanity': [
                '바보', '멍청', '똥', '개', '새끼', '씨발', '병신', '미친', '미쳤',
                '돌았', '정신', '빡', '빡치'
            ]
        }
        
        # LLM 서비스 (나중에 주입)
        self.llm_service = None
    
    def inject_llm_service(self, llm_service):
        """LLM 서비스 주입"""
        self.llm_service = llm_service
    
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
            return max(scores, key=scores.get)
        
        return 'technical'  # 기본값
    
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
            
            # 존댓말 변형
            lambda q: q.replace('요', '').strip(),
            lambda q: q.replace('요', '다').strip(),
            
            # 조사 변형
            lambda q: q.replace('가', '이').strip(),
            lambda q: q.replace('이', '가').strip(),
            lambda q: q.replace('를', '을').strip(),
            lambda q: q.replace('을', '를').strip(),
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
            ]
            
            for pattern in tech_variations:
                try:
                    variation = pattern(question)
                    if len(variation) < 100:  # 너무 길지 않게
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
        
        return unique_variations[:10]  # 최대 10개 변형
    
    async def _classify_with_llm(self, question: str) -> str:
        """LLM을 사용한 문맥 분류"""
        if not self.llm_service:
            return self._classify_by_keywords(question)
        
        try:
            prompt = f"""다음 질문을 4가지 카테고리로 분류해주세요:

- casual: 일상 대화, 인사말, AI 관련 질문
- technical: 기술적 문제 해결, 시스템 관련 질문, 하드웨어/소프트웨어 문제
- non_counseling: 상담 범위를 벗어나는 일반 지식 질문, 역사/지리/과학 등
- profanity: 욕설 및 공격적 표현

질문: "{question}"

답변 형식: casual 또는 technical 또는 non_counseling 또는 profanity
답변만 출력하고 다른 설명은 하지 마세요."""

            response = await self.llm_service.get_conversation_response(prompt)
            response_clean = response.strip().lower()
            
            # 응답 파싱
            if 'casual' in response_clean:
                return 'casual'
            elif 'technical' in response_clean:
                return 'technical'
            elif 'non_counseling' in response_clean:
                return 'non_counseling'
            elif 'profanity' in response_clean:
                return 'profanity'
            else:
                return self._classify_by_keywords(question)
                
        except Exception as e:
            logging.error(f"LLM 분류 실패: {str(e)}")
            return self._classify_by_keywords(question)
    
    async def generate_patterns_from_knowledge_base(self, use_llm: bool = True) -> Dict:
        """knowledge_base에서 context_patterns 생성"""
        logger.info("knowledge_base → context_patterns 변환 시작...")
        
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
            
            # 문맥 분류
            if use_llm and self.llm_service:
                context = await self._classify_with_llm(question)
            else:
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
                    "accuracy": 0.9,
                    "usage_count": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "source": "knowledge_base_generated"
                }
                
                # 중복 체크 후 저장
                existing = await self.pattern_collection.find_one({"pattern": variation})
                if not existing:
                    await self.pattern_collection.insert_one(pattern_doc)
                    total_patterns += 1
            
            # 진행률 출력
            if i % 50 == 0:
                logger.info(f"진행률: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
        
        # 최종 통계
        final_count = await self.pattern_collection.count_documents({})
        
        result = {
            "original_patterns": existing_count,
            "new_patterns_generated": total_patterns,
            "total_patterns": final_count,
            "context_distribution": context_stats,
            "questions_processed": len(questions)
        }
        
        logger.info("=== 변환 완료 ===")
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
        generator = ContextPatternGenerator(db)
        
        # LLM 서비스 주입 (선택사항)
        try:
            from ..dependencies import get_llm_service
            llm_service = await get_llm_service()
            generator.inject_llm_service(llm_service)
            use_llm = True
            print("✅ LLM 서비스 연결됨 - 고정확도 분류 사용")
        except:
            use_llm = False
            print("⚠️ LLM 서비스 연결 실패 - 키워드 기반 분류 사용")
        
        # 1. 패턴 생성
        result = await generator.generate_patterns_from_knowledge_base(use_llm=use_llm)
        
        # 2. 중복 정리
        cleanup_result = await generator.cleanup_duplicate_patterns()
        
        # 3. 최종 결과 출력
        print(f"\n🎉 context_patterns 생성 완료!")
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
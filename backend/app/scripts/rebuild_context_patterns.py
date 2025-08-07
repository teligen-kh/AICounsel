#!/usr/bin/env python3
"""
context_patterns 테이블 완전 재구성 스크립트
knowledge_base의 question을 2-3단어 핵심 문맥 패턴으로 분리
"""

import asyncio
import sys
import os
import re
from datetime import datetime
import logging
from typing import List, Dict, Set

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_database

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextPatternRebuilder:
    """context_patterns 테이블 완전 재구성"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.pattern_collection = db.context_patterns
        
        # 제외할 단어들 (너무 일반적인 단어들)
        self.exclude_words = {
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', '은', '는',
            '있', '없', '하', '되', '되다', '하다', '알', '모르', '보', '보기', '보고', '보면', '보니',
            '문의', '요청', '드립니다', '합니다', '됩니다', '됩니다', '있습니다', '없습니다',
            '어떻게', '무엇', '언제', '어디', '왜', '어떤', '몇', '얼마', '어느', '무슨',
            '문제', '해결', '방법', '설정', '관리', '확인', '체크', '검색', '조회'
        }
        
        # 문맥별 키워드 (기본 분류용)
        self.context_keywords = {
            'technical': [
                '포스', 'pos', '프린터', '스캐너', '키오스크', 'kiosk', '카드', '결제', '결재',
                '설치', '재설치', '업데이트', '오류', '에러', '문제', '안됨', '안돼요',
                '연결', '인터넷', '네트워크', '백업', '복구', '드라이버', '설정',
                '데이터', 'db', '데이터베이스', '바코드', 'qr', 'qr코드', '영수증',
                '출력', '단말기', '리더기', '카드리더기', '포트', 'usb', '엑셀',
                '직인', '도장', '견적서', '거래명세서', '출하단가', '공급자'
            ],
            'casual': [
                '안녕', '반갑', '하이', 'hi', 'hello', '감사', '고마워', '고맙습니다',
                '상담사', '사람', '대화', '연결해줘', '연결해 주세요', '도움', '도와주세요',
                'ai', '인공지능', '로봇', '봇', '봇인가요', '사람인가요'
            ]
        }
    
    def extract_core_patterns(self, text: str) -> List[str]:
        """텍스트에서 2-3단어 핵심 문맥 패턴을 추출합니다."""
        patterns = []
        
        # 텍스트 정리
        text = re.sub(r'[^\w\s가-힣]', ' ', text)  # 특수문자 제거
        text = re.sub(r'\s+', ' ', text).strip()   # 연속 공백 제거
        
        # 단어 분리
        words = text.split()
        
        # 2-3단어 조합 생성
        for i in range(len(words) - 1):
            # 2단어 조합
            pattern_2 = f"{words[i]} {words[i+1]}"
            if self._is_valid_pattern(pattern_2):
                patterns.append(pattern_2)
            
            # 3단어 조합 (가능한 경우)
            if i < len(words) - 2:
                pattern_3 = f"{words[i]} {words[i+1]} {words[i+2]}"
                if self._is_valid_pattern(pattern_3):
                    patterns.append(pattern_3)
        
        return list(set(patterns))  # 중복 제거
    
    def _is_valid_pattern(self, pattern: str) -> bool:
        """패턴이 유효한지 확인합니다."""
        # 너무 짧거나 긴 패턴 제외
        if len(pattern) < 3 or len(pattern) > 20:
            return False
        
        # 제외할 단어만으로 구성된 패턴 제외
        words = pattern.split()
        if all(word in self.exclude_words for word in words):
            return False
        
        # 숫자만으로 구성된 패턴 제외
        if pattern.replace(' ', '').isdigit():
            return False
        
        return True
    
    def classify_context(self, pattern: str) -> str:
        """패턴의 문맥을 분류합니다."""
        pattern_lower = pattern.lower()
        
        # technical 키워드 확인
        for keyword in self.context_keywords['technical']:
            if keyword in pattern_lower:
                return 'technical'
        
        # casual 키워드 확인
        for keyword in self.context_keywords['casual']:
            if keyword in pattern_lower:
                return 'casual'
        
        # 기본값은 technical (상담 관련이므로)
        return 'technical'
    
    async def rebuild_patterns(self) -> Dict:
        """context_patterns 테이블을 완전히 재구성합니다."""
        logger.info("=== context_patterns 테이블 재구성 시작 ===")
        
        # 기존 패턴 모두 삭제
        delete_result = await self.pattern_collection.delete_many({})
        logger.info(f"기존 패턴 {delete_result.deleted_count}개 삭제 완료")
        
        # knowledge_base에서 모든 질문 가져오기
        questions = await self.knowledge_collection.find({}, {"question": 1}).to_list(length=None)
        logger.info(f"knowledge_base에서 {len(questions)}개 질문 로드")
        
        total_patterns = 0
        context_stats = {'technical': 0, 'casual': 0}
        
        # 각 질문에서 패턴 추출
        for i, q_data in enumerate(questions, 1):
            question = q_data.get("question", "")
            if not question:
                continue
            
            # 핵심 패턴 추출
            patterns = self.extract_core_patterns(question)
            
            # 패턴 저장
            for pattern in patterns:
                context = self.classify_context(pattern)
                context_stats[context] += 1
                
                pattern_doc = {
                    "pattern": pattern,
                    "context": context,
                    "original_question": question,
                    "is_active": True,
                    "accuracy": 0.9,
                    "usage_count": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "source": "rebuild_patterns"
                }
                
                # 중복 체크 후 저장
                existing = await self.pattern_collection.find_one({"pattern": pattern})
                if not existing:
                    await self.pattern_collection.insert_one(pattern_doc)
                    total_patterns += 1
            
            # 진행률 출력
            if i % 100 == 0:
                logger.info(f"진행률: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
        
        # 최종 통계
        final_count = await self.pattern_collection.count_documents({})
        
        result = {
            "deleted_patterns": delete_result.deleted_count,
            "new_patterns_generated": total_patterns,
            "total_patterns": final_count,
            "context_distribution": context_stats,
            "questions_processed": len(questions)
        }
        
        logger.info("=== 재구성 완료 ===")
        logger.info(f"삭제된 패턴: {result['deleted_patterns']}개")
        logger.info(f"새로 생성된 패턴: {result['new_patterns_generated']}개")
        logger.info(f"총 패턴: {result['total_patterns']}개")
        logger.info(f"문맥별 분포: {result['context_distribution']}")
        
        return result

async def main():
    """메인 실행 함수"""
    try:
        db = await get_database()
        rebuilder = ContextPatternRebuilder(db)
        
        result = await rebuilder.rebuild_patterns()
        
        print("\n=== 재구성 결과 ===")
        print(f"삭제된 패턴: {result['deleted_patterns']}개")
        print(f"새로 생성된 패턴: {result['new_patterns_generated']}개")
        print(f"총 패턴: {result['total_patterns']}개")
        print(f"문맥별 분포: {result['context_distribution']}")
        
        # 샘플 패턴 출력
        print("\n=== 샘플 패턴 (상위 10개) ===")
        sample_patterns = await db.context_patterns.find({}).limit(10).to_list(length=None)
        for i, pattern in enumerate(sample_patterns, 1):
            print(f"{i}. {pattern['pattern']} -> {pattern['context']}")
        
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 
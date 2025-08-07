#!/usr/bin/env python3
"""
SimpleKoreanAnalyzer를 사용한 context_patterns 재구성 스크립트
knowledge_base의 질문들을 분석하여 정확한 문맥 패턴을 추출합니다.
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Set

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_database
from app.scripts.simple_korean_analyzer import SimpleKoreanAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextPatternsRebuilder:
    """SimpleKoreanAnalyzer를 사용한 context_patterns 재구성기"""
    
    def __init__(self):
        """초기화"""
        self.analyzer = SimpleKoreanAnalyzer()
        self.db = None
        
    async def connect_database(self):
        """데이터베이스 연결"""
        self.db = await get_database()
        logger.info("데이터베이스 연결 완료")
    
    async def get_knowledge_base_questions(self) -> List[str]:
        """knowledge_base에서 질문들을 가져옵니다."""
        try:
            cursor = self.db.knowledge_base.find({}, {"question": 1})
            questions = []
            async for doc in cursor:
                if doc.get('question'):
                    questions.append(doc['question'])
            
            logger.info(f"knowledge_base에서 {len(questions)}개의 질문을 가져왔습니다.")
            return questions
            
        except Exception as e:
            logger.error(f"knowledge_base 조회 중 오류 발생: {e}")
            return []
    
    async def clear_context_patterns(self):
        """기존 context_patterns 테이블을 비웁니다."""
        try:
            result = await self.db.context_patterns.delete_many({})
            logger.info(f"기존 context_patterns {result.deleted_count}개 삭제 완료")
        except Exception as e:
            logger.error(f"context_patterns 삭제 중 오류 발생: {e}")
    
    def extract_context_patterns(self, questions: List[str]) -> Dict[str, List[str]]:
        """질문들에서 문맥 패턴을 추출합니다."""
        logger.info("문맥 패턴 추출 시작...")
        
        # SimpleKoreanAnalyzer로 분석
        analysis_results = self.analyzer.analyze_knowledge_base(questions)
        
        # 기술적 패턴들을 context_patterns로 변환
        context_patterns = []
        for pattern in analysis_results['technical_patterns']:
            context_patterns.append({
                'pattern': pattern,
                'category': 'technical',
                'priority': 1,
                'description': f'기술적 패턴: {pattern}'
            })
        
        # 명사 조합도 추가 (우선순위 낮게)
        for pattern in analysis_results['noun_combinations']:
            # 이미 기술적 패턴에 포함되지 않은 것만 추가
            if not any(p['pattern'] == pattern for p in context_patterns):
                context_patterns.append({
                    'pattern': pattern,
                    'category': 'technical',
                    'priority': 2,
                    'description': f'명사 조합: {pattern}'
                })
        
        logger.info(f"총 {len(context_patterns)}개의 문맥 패턴 추출 완료")
        return context_patterns
    
    async def insert_context_patterns(self, patterns: List[Dict]):
        """context_patterns 테이블에 패턴들을 삽입합니다."""
        try:
            if patterns:
                result = await self.db.context_patterns.insert_many(patterns)
                logger.info(f"context_patterns에 {len(result.inserted_ids)}개 패턴 삽입 완료")
            else:
                logger.warning("삽입할 패턴이 없습니다.")
        except Exception as e:
            logger.error(f"context_patterns 삽입 중 오류 발생: {e}")
    
    async def rebuild_context_patterns(self):
        """context_patterns 테이블을 완전히 재구성합니다."""
        logger.info("=== context_patterns 재구성 시작 ===")
        
        # 1. 데이터베이스 연결
        await self.connect_database()
        
        # 2. knowledge_base에서 질문들 가져오기
        questions = await self.get_knowledge_base_questions()
        if not questions:
            logger.error("질문을 가져올 수 없습니다.")
            return
        
        # 3. 기존 context_patterns 삭제
        await self.clear_context_patterns()
        
        # 4. 문맥 패턴 추출
        patterns = self.extract_context_patterns(questions)
        
        # 5. context_patterns 테이블에 삽입
        await self.insert_context_patterns(patterns)
        
        # 6. 결과 확인
        await self.verify_results()
        
        logger.info("=== context_patterns 재구성 완료 ===")
    
    async def verify_results(self):
        """재구성 결과를 확인합니다."""
        try:
            count = await self.db.context_patterns.count_documents({})
            logger.info(f"현재 context_patterns 테이블에 {count}개의 패턴이 있습니다.")
            
            # 샘플 데이터 확인
            sample_patterns = await self.db.context_patterns.find().limit(10).to_list(length=10)
            logger.info("샘플 패턴들:")
            for pattern in sample_patterns:
                logger.info(f"  - {pattern['pattern']} ({pattern['category']}, 우선순위: {pattern['priority']})")
                
        except Exception as e:
            logger.error(f"결과 확인 중 오류 발생: {e}")


async def main():
    """메인 함수"""
    rebuilder = ContextPatternsRebuilder()
    await rebuilder.rebuild_context_patterns()


if __name__ == "__main__":
    asyncio.run(main()) 
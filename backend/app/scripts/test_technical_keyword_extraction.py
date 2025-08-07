#!/usr/bin/env python3
"""
LLM을 사용한 technical 키워드 추출 테스트 모듈
knowledge_base에서 랜덤 10개 질문을 가져와서 LLM이 technical 키워드를 추출하는 기능을 테스트
"""

import asyncio
import motor.motor_asyncio
import random
import logging
from typing import List, Dict, Set
import sys
import os

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.llm_service import LLMService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalKeywordExtractor:
    """LLM을 사용한 technical 키워드 추출기"""
    
    def __init__(self, db, llm_service):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.llm_service = llm_service
        
    async def get_random_questions(self, count: int = 10) -> List[str]:
        """knowledge_base에서 랜덤으로 질문들을 가져옵니다."""
        try:
            # 모든 질문 가져오기
            all_questions = await self.knowledge_collection.find({}, {"question": 1}).to_list(length=None)
            
            if not all_questions:
                logger.error("knowledge_base에 질문이 없습니다.")
                return []
            
            # 랜덤으로 선택
            selected_questions = random.sample(all_questions, min(count, len(all_questions)))
            questions = [q['question'] for q in selected_questions]
            
            logger.info(f"랜덤 {len(questions)}개 질문 선택 완료")
            return questions
            
        except Exception as e:
            logger.error(f"랜덤 질문 가져오기 실패: {e}")
            return []
    
    async def extract_technical_keywords_with_llm(self, question: str) -> List[str]:
        """LLM을 사용해서 질문에서 technical 키워드를 추출합니다."""
        try:
            prompt = f"""
다음 질문에서 기술적 문제나 상담과 관련된 핵심 키워드들을 추출해주세요.
키워드는 2-4개 정도로 추출하고, 쉼표로 구분해서 답변해주세요.

질문: {question}

추출된 키워드들:
"""
            
            response = await self.llm_service._handle_pure_llm_message(prompt)
            
            # 응답에서 키워드 추출
            keywords = self._parse_keywords_from_response(response)
            
            logger.info(f"질문: {question[:50]}...")
            logger.info(f"추출된 키워드: {keywords}")
            
            return keywords
            
        except Exception as e:
            logger.error(f"LLM 키워드 추출 실패: {e}")
            return []
    
    def _parse_keywords_from_response(self, response: str) -> List[str]:
        """LLM 응답에서 키워드를 파싱합니다."""
        try:
            # 응답 정리
            response = response.strip()
            
            # 쉼표로 분리
            keywords = [kw.strip() for kw in response.split(',')]
            
            # 빈 문자열 제거
            keywords = [kw for kw in keywords if kw]
            
            # 2-4개로 제한
            return keywords[:4]
            
        except Exception as e:
            logger.error(f"키워드 파싱 실패: {e}")
            return []
    
    async def test_keyword_extraction(self):
        """전체 테스트를 실행합니다."""
        logger.info("=== LLM Technical 키워드 추출 테스트 시작 ===")
        
        # 1. 랜덤 질문 가져오기
        questions = await self.get_random_questions(10)
        if not questions:
            logger.error("질문을 가져올 수 없습니다.")
            return
        
        # 2. 각 질문에서 키워드 추출
        results = []
        for i, question in enumerate(questions, 1):
            logger.info(f"\n--- 질문 {i} ---")
            logger.info(f"질문: {question}")
            
            keywords = await self.extract_technical_keywords_with_llm(question)
            
            results.append({
                'question': question,
                'keywords': keywords
            })
            
            # 잠시 대기 (LLM 부하 방지)
            await asyncio.sleep(1)
        
        # 3. 결과 요약
        logger.info("\n=== 테스트 결과 요약 ===")
        all_keywords = set()
        for result in results:
            all_keywords.update(result['keywords'])
        
        logger.info(f"총 추출된 고유 키워드 수: {len(all_keywords)}")
        logger.info(f"추출된 키워드들: {sorted(all_keywords)}")
        
        # 4. 상세 결과 출력
        logger.info("\n=== 상세 결과 ===")
        for i, result in enumerate(results, 1):
            logger.info(f"질문 {i}: {result['question'][:50]}...")
            logger.info(f"키워드: {result['keywords']}")
            logger.info("---")
        
        return results

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # LLM 서비스 초기화
        llm_service = LLMService()
        logger.info("LLM 서비스 초기화 완료")
        
        # 키워드 추출기 생성
        extractor = TechnicalKeywordExtractor(db, llm_service)
        
        # 테스트 실행
        results = await extractor.test_keyword_extraction()
        
        if results:
            logger.info("✅ 테스트 완료!")
        else:
            logger.error("❌ 테스트 실패!")
            
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
전체 technical 키워드 추출 및 context_patterns 저장 모듈
1. knowledge_base의 모든 질문 가져오기
2. LLM으로 technical 키워드 추출
3. 중복 제거
4. context_patterns 테이블에 저장
"""

import asyncio
import motor.motor_asyncio
import logging
from typing import List, Dict, Set
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.llm_service import LLMService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullTechnicalKeywordExtractor:
    """전체 technical 키워드 추출기"""
    
    def __init__(self, db, llm_service):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.pattern_collection = db.context_patterns
        self.llm_service = llm_service
        
    async def get_all_questions(self) -> List[str]:
        """knowledge_base에서 모든 질문을 가져옵니다."""
        try:
            logger.info("knowledge_base에서 모든 질문을 가져오는 중...")
            
            # 모든 질문 가져오기
            all_questions = await self.knowledge_collection.find({}, {"question": 1}).to_list(length=None)
            
            if not all_questions:
                logger.error("knowledge_base에 질문이 없습니다.")
                return []
            
            questions = [q['question'] for q in all_questions]
            logger.info(f"총 {len(questions)}개의 질문을 가져왔습니다.")
            
            return questions
            
        except Exception as e:
            logger.error(f"질문 가져오기 실패: {e}")
            return []
    
    async def extract_technical_keywords_with_llm(self, question: str) -> List[str]:
        """LLM을 사용해서 질문에서 technical 키워드를 추출합니다."""
        try:
            prompt = f"""
다음 질문에서 기술적 문제나 상담과 관련된 핵심 키워드들을 추출해주세요.
키워드는 2-4개 정도로 추출하고, 쉼표로 구분해서 답변해주세요.
기술적 문제나 상담과 관련 없는 일반적인 단어는 제외해주세요.

질문: {question}

추출된 키워드들:
"""
            
            response = await self.llm_service._handle_pure_llm_message(prompt)
            
            # 응답에서 키워드 추출
            keywords = self._parse_keywords_from_response(response)
            
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
    
    async def process_all_questions(self, questions: List[str]) -> List[Dict]:
        """모든 질문을 처리하여 키워드를 추출합니다."""
        logger.info("=== 모든 질문에서 키워드 추출 시작 ===")
        
        results = []
        total_questions = len(questions)
        
        for i, question in enumerate(questions, 1):
            logger.info(f"처리 중: {i}/{total_questions} - {question[:50]}...")
            
            keywords = await self.extract_technical_keywords_with_llm(question)
            
            if keywords:
                results.append({
                    'question': question,
                    'keywords': keywords
                })
            
            # 진행률 표시
            if i % 10 == 0:
                logger.info(f"진행률: {i}/{total_questions} ({i/total_questions*100:.1f}%)")
            
            # LLM 부하 방지를 위한 대기
            await asyncio.sleep(0.5)
        
        logger.info(f"키워드 추출 완료: {len(results)}개 질문에서 키워드 추출됨")
        return results
    
    def remove_duplicates(self, results: List[Dict]) -> Set[str]:
        """중복을 제거하고 고유한 키워드들을 반환합니다."""
        logger.info("중복 제거 중...")
        
        all_keywords = set()
        for result in results:
            all_keywords.update(result['keywords'])
        
        logger.info(f"중복 제거 완료: {len(all_keywords)}개의 고유 키워드")
        return all_keywords
    
    async def save_to_context_patterns(self, keywords: Set[str]) -> bool:
        """추출된 키워드들을 context_patterns 테이블에 저장합니다."""
        try:
            logger.info("context_patterns 테이블에 저장 중...")
            
            # 기존 데이터 확인
            existing_count = await self.pattern_collection.count_documents({})
            logger.info(f"기존 context_patterns 문서 수: {existing_count}")
            
            # 새로운 패턴 데이터 생성
            patterns_to_insert = []
            for keyword in keywords:
                pattern_data = {
                    'pattern': keyword,
                    'context': 'technical',
                    'priority': 1,
                    'description': f'LLM 추출 technical 키워드: {keyword}',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'source': 'llm_extraction'
                }
                patterns_to_insert.append(pattern_data)
            
            # 일괄 삽입
            if patterns_to_insert:
                result = await self.pattern_collection.insert_many(patterns_to_insert)
                inserted_count = len(result.inserted_ids)
                logger.info(f"저장 완료: {inserted_count}개의 패턴이 저장됨")
                
                # 최종 확인
                final_count = await self.pattern_collection.count_documents({})
                logger.info(f"최종 context_patterns 문서 수: {final_count}")
                
                return True
            else:
                logger.warning("저장할 패턴이 없습니다.")
                return False
                
        except Exception as e:
            logger.error(f"context_patterns 저장 실패: {e}")
            return False
    
    async def run_full_process(self):
        """전체 프로세스를 실행합니다."""
        logger.info("=== 전체 Technical 키워드 추출 프로세스 시작 ===")
        
        try:
            # 1단계: 모든 질문 가져오기
            questions = await self.get_all_questions()
            if not questions:
                logger.error("질문을 가져올 수 없습니다.")
                return False
            
            # 2단계: LLM으로 키워드 추출
            results = await self.process_all_questions(questions)
            if not results:
                logger.error("키워드 추출에 실패했습니다.")
                return False
            
            # 3단계: 중복 제거
            unique_keywords = self.remove_duplicates(results)
            if not unique_keywords:
                logger.error("고유한 키워드가 없습니다.")
                return False
            
            # 4단계: context_patterns에 저장
            success = await self.save_to_context_patterns(unique_keywords)
            
            if success:
                logger.info("✅ 전체 프로세스 완료!")
                logger.info(f"총 처리된 질문 수: {len(questions)}")
                logger.info(f"키워드 추출된 질문 수: {len(results)}")
                logger.info(f"최종 고유 키워드 수: {len(unique_keywords)}")
                return True
            else:
                logger.error("❌ context_patterns 저장에 실패했습니다.")
                return False
                
        except Exception as e:
            logger.error(f"전체 프로세스 실행 중 오류: {e}")
            return False

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # LLM 서비스 초기화
        llm_service = LLMService()
        logger.info("LLM 서비스 초기화 완료")
        
        # 전체 프로세스 실행기 생성
        extractor = FullTechnicalKeywordExtractor(db, llm_service)
        
        # 전체 프로세스 실행
        success = await extractor.run_full_process()
        
        if success:
            logger.info("🎉 전체 작업이 성공적으로 완료되었습니다!")
        else:
            logger.error("❌ 전체 작업에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
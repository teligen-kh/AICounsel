#!/usr/bin/env python3
"""
knowledge_base 검색 테스트 모듈
1. technical로 분류된 질문에서 키워드 추출
2. knowledge_base 테이블의 question 컬럼 검색
3. LLM이 가장 적절한 답변 선택
"""

import asyncio
import motor.motor_asyncio
import logging
from typing import List, Dict, Optional, Tuple
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.context_aware_classifier import ContextAwareClassifier, InputType
from app.services.llm_service import LLMService
from app.services.mongodb_search_service import MongoDBSearchService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeBaseSearchTester:
    """knowledge_base 검색 테스트기"""
    
    def __init__(self, db, llm_service):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        self.classifier = ContextAwareClassifier(db)
        self.classifier.inject_llm_service(llm_service)
        self.search_service = MongoDBSearchService(db)
        self.llm_service = llm_service
        
    def extract_keywords_from_technical_question(self, question: str, classification_details: Dict) -> List[str]:
        """technical 질문에서 키워드 추출"""
        keywords = []
        
        # 1. 분류 과정에서 사용된 키워드들
        if 'matched_words' in classification_details:
            keywords.extend(classification_details['matched_words'])
        
        # 2. 명확한 technical 키워드들
        technical_keywords = [
            '포스', 'pos', '프린터', '키오스크', '카드', '결제', '영수증', '바코드', 'qr코드',
            '설치', '설정', '오류', '문제', '드라이버', '재설치', '백업', '복구',
            '프로그램', '소프트웨어', '하드웨어', '시스템', '클라우드',
            '법인결재', '결재', '매출', '매입', '재고', '회계', '코드관리',
            '상품', '엑셀', '쇼핑몰', '매출작업', '통신', '에러', '실패'
        ]
        
        question_lower = question.lower()
        for keyword in technical_keywords:
            if keyword.lower() in question_lower:
                keywords.append(keyword)
        
        # 중복 제거
        keywords = list(set(keywords))
        return keywords
    
    async def search_knowledge_base(self, keywords: List[str]) -> List[Dict]:
        """키워드로 knowledge_base 검색"""
        try:
            logger.info(f"검색 키워드: {keywords}")
            
            # 키워드를 하나의 쿼리로 결합
            query = " ".join(keywords)
            
            # 검색 서비스 사용
            answer = await self.search_service.search_answer(query)
            
            if answer:
                # 검색 결과를 표준 형식으로 변환
                search_results = [{
                    'question': query,
                    'answer': answer,
                    'score': 1.0
                }]
                logger.info(f"검색 결과: 1개 발견")
                return search_results
            else:
                logger.info(f"검색 결과: 0개 발견")
                return []
            
        except Exception as e:
            logger.error(f"knowledge_base 검색 실패: {e}")
            return []
    
    async def select_best_answer_with_llm(self, question: str, search_results: List[Dict]) -> Optional[Dict]:
        """LLM을 사용해서 가장 적절한 답변 선택"""
        try:
            if not search_results:
                logger.warning("검색 결과가 없습니다.")
                return None
            
            # 검색 결과를 LLM이 평가할 수 있는 형태로 변환
            candidates = []
            for i, result in enumerate(search_results[:5]):  # 상위 5개만 평가
                candidates.append({
                    'id': i + 1,
                    'question': result.get('question', ''),
                    'answer': result.get('answer', ''),
                    'score': result.get('score', 0)
                })
            
            # LLM 프롬프트 생성
            prompt = f"""다음 고객 질문에 대해 가장 적절한 답변을 선택해주세요.

고객 질문: "{question}"

후보 답변들:
"""
            
            for candidate in candidates:
                prompt += f"""
{candidate['id']}. 질문: {candidate['question']}
   답변: {candidate['answer']}
   점수: {candidate['score']}
"""
            
            prompt += """
위 후보들 중에서 고객 질문에 가장 적절한 답변의 번호만 입력해주세요.
답변 형식: 1 또는 2 또는 3 또는 4 또는 5
"""
            
            # LLM 호출
            response = await self.llm_service._handle_pure_llm_message(prompt)
            response_clean = response.strip()
            
            # 응답에서 번호 추출
            try:
                selected_id = int(response_clean)
                if 1 <= selected_id <= len(candidates):
                    selected_candidate = candidates[selected_id - 1]
                    logger.info(f"LLM이 선택한 답변 ID: {selected_id}")
                    return selected_candidate
                else:
                    logger.warning(f"LLM 응답이 유효하지 않음: {response_clean}")
                    # 점수가 가장 높은 답변 선택
                    best_result = max(candidates, key=lambda x: x['score'])
                    logger.info(f"점수 기반으로 최적 답변 선택: ID {best_result['id']}")
                    return best_result
            except ValueError:
                logger.warning(f"LLM 응답을 숫자로 변환할 수 없음: {response_clean}")
                # 점수가 가장 높은 답변 선택
                best_result = max(candidates, key=lambda x: x['score'])
                logger.info(f"점수 기반으로 최적 답변 선택: ID {best_result['id']}")
                return best_result
                
        except Exception as e:
            logger.error(f"LLM 답변 선택 중 오류: {e}")
            return None
    
    async def format_response_for_customer(self, question: str, selected_answer: Dict) -> str:
        """고객에게 전달할 응답 포맷팅"""
        try:
            if not selected_answer:
                return "죄송합니다. 해당 질문에 대한 답변을 찾을 수 없습니다. 전문 상담사에게 문의해주세요."
            
            # LLM을 사용해서 답변을 친절하게 변형
            prompt = f"""다음 답변을 고객에게 친절하고 이해하기 쉽게 다시 작성해주세요.
원래 질문: "{question}"
원래 답변: "{selected_answer['answer']}"

요구사항:
1. 2-3문장으로 간결하게 작성
2. 친근하고 도움이 되는 톤으로 작성
3. 구체적인 단계나 방법이 있다면 명확하게 설명
4. "~하세요", "~해주세요" 형태로 종결

답변:"""
            
            response = await self.llm_service._handle_pure_llm_message(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"응답 포맷팅 중 오류: {e}")
            return selected_answer.get('answer', '죄송합니다. 답변을 처리하는 중 오류가 발생했습니다.')
    
    async def test_knowledge_base_search(self, test_questions: List[str]):
        """knowledge_base 검색 테스트 실행"""
        logger.info("=== knowledge_base 검색 테스트 시작 ===")
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                # 1단계: 질문 분류
                input_type, classification_details = await self.classifier.classify_input(question)
                logger.info(f"분류 결과: {input_type.value}")
                logger.info(f"분류 상세: {classification_details}")
                
                # technical이 아니면 건너뛰기
                if input_type != InputType.TECHNICAL:
                    logger.info(f"Technical 분류가 아니므로 건너뜀: {input_type.value}")
                    continue
                
                # 2단계: 키워드 추출
                keywords = self.extract_keywords_from_technical_question(question, classification_details)
                logger.info(f"추출된 키워드: {keywords}")
                
                # 3단계: knowledge_base 검색
                search_results = await self.search_knowledge_base(keywords)
                
                if not search_results:
                    logger.warning("검색 결과가 없습니다.")
                    continue
                
                # 4단계: LLM으로 최적 답변 선택
                selected_answer = await self.select_best_answer_with_llm(question, search_results)
                
                if not selected_answer:
                    logger.warning("적절한 답변을 선택할 수 없습니다.")
                    continue
                
                # 5단계: 고객 응답 포맷팅
                customer_response = await self.format_response_for_customer(question, selected_answer)
                
                # 결과 출력
                logger.info(f"선택된 답변 질문: {selected_answer['question']}")
                logger.info(f"선택된 답변 점수: {selected_answer['score']}")
                logger.info(f"고객 응답: {customer_response}")
                
            except Exception as e:
                logger.error(f"테스트 {i} 실행 중 오류: {e}")
        
        logger.info("\n=== knowledge_base 검색 테스트 완료 ===")

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # LLM 서비스 초기화
        llm_service = LLMService()
        logger.info("LLM 서비스 초기화 완료")
        
        # 테스트기 생성
        tester = KnowledgeBaseSearchTester(db, llm_service)
        
        # 테스트 질문들 (technical 분류가 될 것들)
        test_questions = [
            "프린터 용지 출력이 안되고 빨간 불이 깜빡이는 문제",
            "POS 시스템 백업 방법",
            "프로그램 재설치문의",
            "판매관리비 코드관리에서 계정 항목이 안보인다고 하심",
            "클라우드 설치요청",
            "바코드프린터 새로 구매했어요 설치요청 드립니다",
            "상품엑셀 저장이 안됩니다",
            "쇼핑몰을 저희가 확인하는 방법?",
            "매출작업을 해놧는데 손님이 해당매출을 한개로 만들어달라고하는데 매출을 합칠수있나요?",
            "키오스크에서 카드결제를 하는중 통신에러 통신실패라고 나온다고 하는데 무슨문제인가요?"
        ]
        
        # 테스트 실행
        await tester.test_knowledge_base_search(test_questions)
        
        logger.info("🎉 knowledge_base 검색 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
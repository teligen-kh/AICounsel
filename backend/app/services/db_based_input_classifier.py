"""
DB 기반 입력 분류기 모듈
MongoDB의 키워드 테이블을 활용하여 동적으로 입력을 분류하는 시스템
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

class InputType(Enum):
    """입력 타입 분류"""
    CASUAL = "casual"              # 일상 대화 (인사말 포함)
    TECHNICAL = "technical"        # 기술적 질문
    NON_COUNSELING = "non_counseling"  # 비상담 질문
    PROFANITY = "profanity"        # 욕설
    UNKNOWN = "unknown"            # 기타

class DBBasedInputClassifier:
    """DB 기반 사용자 입력 필터링 및 분류"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        DB 기반 입력 분류기 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결 인스턴스
        """
        self.db = db
        self.keyword_collection = db.input_keywords
        self.cached_keywords = {}  # 키워드 캐시
        self.cache_updated = False
        
    async def load_keywords_from_db(self) -> Dict[str, List[str]]:
        """DB에서 키워드를 로드하여 캐시에 저장"""
        try:
            if self.cache_updated:
                return self.cached_keywords
            
            # DB에서 모든 키워드 카테고리 가져오기
            categories = {}
            async for item in self.keyword_collection.find({}):
                category = item.get('category', 'unknown')
                keywords = item.get('keywords', [])
                categories[category] = keywords
            
            # 캐시 업데이트
            self.cached_keywords = categories
            self.cache_updated = True
            
            logging.info(f"DB에서 {len(categories)}개 카테고리의 키워드를 로드했습니다.")
            for category, keywords in categories.items():
                logging.info(f"- {category}: {len(keywords)}개 키워드")
            
            return categories
            
        except Exception as e:
            logging.error(f"DB에서 키워드 로드 실패: {str(e)}")
            return {}
    
    async def classify_input(self, user_input: str) -> Tuple[InputType, Dict[str, any]]:
        """
        사용자 입력을 분류하고 결과 반환
        
        Args:
            user_input: 사용자 입력 텍스트
            
        Returns:
            Tuple[InputType, Dict]: 분류 결과와 상세 정보
        """
        try:
            # DB에서 키워드 로드
            categories = await self.load_keywords_from_db()
            input_lower = user_input.lower().strip()
            
            # 욕설 체크 (가장 우선순위)
            if 'profanity' in categories:
                profanity_keywords = categories['profanity']
                matched_profanity = self._find_matched_words(input_lower, profanity_keywords)
                if matched_profanity:
                    return InputType.PROFANITY, {
                        "reason": "욕설 감지",
                        "matched_words": matched_profanity,
                        "source": "db_keywords"
                    }
            
            # 비상담 질문 체크
            if 'non_counseling' in categories:
                non_counseling_keywords = categories['non_counseling']
                matched_non_counseling = self._find_matched_words(input_lower, non_counseling_keywords)
                if matched_non_counseling:
                    return InputType.NON_COUNSELING, {
                        "reason": "상담 범위 외 질문",
                        "matched_words": matched_non_counseling,
                        "source": "db_keywords"
                    }
            
            # 일상 대화 체크 (인사말 포함)
            if 'casual' in categories:
                casual_keywords = categories['casual']
                matched_casual = self._find_matched_words(input_lower, casual_keywords)
                if matched_casual:
                    return InputType.CASUAL, {
                        "reason": "일상 대화 또는 인사말",
                        "matched_words": matched_casual,
                        "source": "db_keywords"
                    }
            
            # 기술적 질문 체크
            if 'technical' in categories:
                technical_keywords = categories['technical']
                matched_technical = self._find_matched_words(input_lower, technical_keywords)
                if matched_technical:
                    return InputType.TECHNICAL, {
                        "reason": "기술적 질문",
                        "matched_words": matched_technical,
                        "source": "db_keywords"
                    }
            
            # 분류되지 않은 경우
            return InputType.UNKNOWN, {
                "reason": "분류 불가",
                "matched_words": [],
                "source": "db_keywords"
            }
            
        except Exception as e:
            logging.error(f"입력 분류 중 오류: {str(e)}")
            return InputType.UNKNOWN, {
                "reason": "오류 발생",
                "matched_words": [],
                "source": "error"
            }
    
    def _find_matched_words(self, text: str, keywords: List[str]) -> List[str]:
        """텍스트에서 매칭되는 키워드를 찾습니다."""
        matched = []
        for keyword in keywords:
            if keyword.lower() in text:
                matched.append(keyword)
        return matched
    
    async def add_keyword(self, category: str, keyword: str) -> bool:
        """
        새로운 키워드를 DB에 추가
        
        Args:
            category: 키워드 카테고리
            keyword: 추가할 키워드
            
        Returns:
            bool: 추가 성공 여부
        """
        try:
            # 기존 카테고리에 키워드 추가
            result = await self.keyword_collection.update_one(
                {"category": category},
                {"$addToSet": {"keywords": keyword}}
            )
            
            if result.modified_count > 0:
                # 캐시 무효화
                self.cache_updated = False
                logging.info(f"키워드 추가 성공: {category} - {keyword}")
                return True
            else:
                logging.warning(f"키워드 추가 실패: {category} - {keyword}")
                return False
                
        except Exception as e:
            logging.error(f"키워드 추가 중 오류: {str(e)}")
            return False
    
    async def remove_keyword(self, category: str, keyword: str) -> bool:
        """
        키워드를 DB에서 제거
        
        Args:
            category: 키워드 카테고리
            keyword: 제거할 키워드
            
        Returns:
            bool: 제거 성공 여부
        """
        try:
            # 기존 카테고리에서 키워드 제거
            result = await self.keyword_collection.update_one(
                {"category": category},
                {"$pull": {"keywords": keyword}}
            )
            
            if result.modified_count > 0:
                # 캐시 무효화
                self.cache_updated = False
                logging.info(f"키워드 제거 성공: {category} - {keyword}")
                return True
            else:
                logging.warning(f"키워드 제거 실패: {category} - {keyword}")
                return False
                
        except Exception as e:
            logging.error(f"키워드 제거 중 오류: {str(e)}")
            return False
    
    async def get_response_template(self, input_type: InputType, company_name: str = "텔리젠") -> str:
        """입력 타입에 따른 응답 템플릿 반환"""
        templates = {
            InputType.PROFANITY: f"욕설을 하시면 응대를 할 수 없습니다. 30분 후 재문의 바랍니다.",
            InputType.NON_COUNSELING: f"저는 {company_name} AI 상담사로 해당 질문은 상담 범위를 벗어나 답변 드릴 수 없습니다.",
            InputType.CASUAL: f"안녕하세요! {company_name} AI 상담사입니다. 포스 시스템과 관련된 질문에 답변해드릴 수 있어요.",
            InputType.TECHNICAL: f"기술적 질문이시군요. {company_name} 상담사가 도와드리겠습니다.",
            InputType.UNKNOWN: f"안녕하세요! {company_name} AI 상담사입니다. 포스 시스템과 관련된 질문에 답변해드릴 수 있어요."
        }
        
        return templates.get(input_type, templates[InputType.UNKNOWN])
    
    async def refresh_cache(self):
        """키워드 캐시를 새로고침합니다."""
        self.cache_updated = False
        await self.load_keywords_from_db()
        logging.info("키워드 캐시를 새로고침했습니다.") 
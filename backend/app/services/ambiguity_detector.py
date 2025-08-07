#!/usr/bin/env python3
"""
모호함 감지 모듈
질문의 모호함을 분석하고 키워드 부족이나 불완전한 표현을 감지
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class AmbiguityDetector:
    """모호함 감지기"""
    
    def __init__(self):
        # 모호한 표현들
        self.ambiguous_expressions = [
            '이거', '저거', '그거', '이것', '저것', '그것',
            '이런', '저런', '그런', '이런 식', '저런 식',
            '이상한', '뭔가', '뭔지', '어떤', '어떻게',
            '바꾸고 싶어', '하고 싶어', '원해', '필요해'
        ]
        
        # 불완전한 표현들
        self.incomplete_expressions = [
            '안 돼', '안 되', '안 됨', '안 됩니다',
            '문제', '오류', '에러', '실패', '안됨',
            '도와줘', '도와주세요', '어떻게', '어떡해'
        ]
        
        # 최소 키워드 수 (technical 질문 기준)
        self.min_technical_keywords = 2
        
        # technical 키워드들
        self.technical_keywords = [
            '포스', 'pos', '프린터', '키오스크', '카드', '결제', '영수증', '바코드', 'qr코드',
            '설치', '설정', '오류', '문제', '드라이버', '재설치', '백업', '복구',
            '프로그램', '소프트웨어', '하드웨어', '시스템', '클라우드',
            '법인결재', '결재', '매출', '매입', '재고', '회계', '코드관리',
            '상품', '엑셀', '쇼핑몰', '매출작업', '통신', '에러', '실패',
            '견적서', '거래명세서', '직인', '도장', '단위', '상품코드'
        ]
    
    def is_ambiguous(self, question: str) -> bool:
        """질문이 모호한지 판단"""
        try:
            question_lower = question.lower()
            
            # 1. 모호한 표현 체크
            if self._has_ambiguous_expressions(question_lower):
                logger.info(f"모호한 표현 감지: {question}")
                return True
            
            # 2. 불완전한 표현 체크
            if self._has_incomplete_expressions(question_lower):
                logger.info(f"불완전한 표현 감지: {question}")
                return True
            
            # 3. 키워드 부족 체크
            if self._has_insufficient_keywords(question_lower):
                logger.info(f"키워드 부족 감지: {question}")
                return True
            
            # 4. 너무 짧은 질문 체크
            if len(question.strip()) < 10:
                logger.info(f"너무 짧은 질문: {question}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"모호함 감지 중 오류: {e}")
            return False
    
    def _has_ambiguous_expressions(self, question: str) -> bool:
        """모호한 표현이 있는지 체크"""
        for expression in self.ambiguous_expressions:
            if expression in question:
                return True
        return False
    
    def _has_incomplete_expressions(self, question: str) -> bool:
        """불완전한 표현이 있는지 체크"""
        for expression in self.incomplete_expressions:
            if expression in question:
                return True
        return False
    
    def _has_insufficient_keywords(self, question: str) -> bool:
        """technical 키워드가 부족한지 체크"""
        found_keywords = []
        for keyword in self.technical_keywords:
            if keyword.lower() in question:
                found_keywords.append(keyword)
        
        return len(found_keywords) < self.min_technical_keywords
    
    def get_ambiguity_reason(self, question: str) -> str:
        """모호함의 이유를 반환"""
        question_lower = question.lower()
        
        if self._has_ambiguous_expressions(question_lower):
            return "모호한 표현 사용"
        elif self._has_incomplete_expressions(question_lower):
            return "불완전한 표현 사용"
        elif self._has_insufficient_keywords(question_lower):
            return "키워드 부족"
        elif len(question.strip()) < 10:
            return "질문이 너무 짧음"
        else:
            return "알 수 없음"
    
    def get_missing_keywords(self, question: str) -> List[str]:
        """부족한 키워드들을 반환"""
        question_lower = question.lower()
        found_keywords = []
        
        for keyword in self.technical_keywords:
            if keyword.lower() in question_lower:
                found_keywords.append(keyword)
        
        # 부족한 키워드들 (예시)
        missing_keywords = []
        if '견적서' in question_lower and '상품코드' not in question_lower:
            missing_keywords.append('상품코드')
        if '직인' in question_lower and '고객' not in question_lower:
            missing_keywords.append('고객 정보')
        if '설정' in question_lower and '어떤' not in question_lower:
            missing_keywords.append('구체적인 설정 항목')
        
        return missing_keywords 
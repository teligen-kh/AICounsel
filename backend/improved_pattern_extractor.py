#!/usr/bin/env python3
"""
개선된 2-3단어 핵심 문맥 패턴 추출기
의미 있는 핵심 패턴만 추출하고 접미사 제거
"""

import asyncio
import sys
import os
import re
import random
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database

class ImprovedPatternExtractor:
    """개선된 2-3단어 핵심 문맥 패턴 추출기"""
    
    def __init__(self):
        # 핵심 기술 용어 사전 (technical 분류에 사용할 단어들)
        self.technical_keywords = {
            # 하드웨어
            '포스', 'pos', '프린터', '스캐너', '키오스크', 'kiosk', '카드리더기', '단말기', '장비', '기기',
            
            # 소프트웨어
            '프로그램', '소프트웨어', '드라이버', '설치', '재설치', '업데이트',
            
            # 시스템
            '시스템', '네트워크', '연결', '인터넷', '설정', '관리', '로그인', '비밀번호', '계정',
            
            # 문제 해결
            '오류', '에러', '문제', '해결', '수정', '고장', '안됨', '안되', '오류코드', '코드',
            
            # 데이터
            '데이터', '백업', '복구', '저장', '삭제', '이동', '업로드', '다운로드',
            
            # 결제
            '결제', '카드', '영수증', '바코드', 'qr', 'qr코드', '직인', '도장',
            
            # 비즈니스
            '매출', '매출작업', '매출내역', '출하단가', '공급자', '고객등록', '견적', '견적서', '거래명세서',
            
            # 기타 기술
            '원격', '접속', '권한', '보안', '클라우드', '엑셀', '엑셀변환', '직인숨김',
            
            # 쇼핑몰
            '쇼핑몰', '주문', '주문서', '확인', '조회', '검색'
        }
        
        # 제거할 조사들 (의미 없는 단어들)
        self.particles_to_remove = [
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', '은', '는',
            '도', '만', '부터', '까지', '마다', '마다', '마다', '마다', '마다', '마다', '마다', '마다',
            '나', '나', '나', '나', '나', '나', '나', '나', '나', '나', '나', '나', '나', '나', '나',
            '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도',
            '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도', '라도'
        ]
        
        # 제거할 접미사들 (의미 없는 단어들)
        self.suffixes_to_remove = [
            # 요청/부탁 접미사
            '요', '해주세요', '부탁해요', '빨리요', '바빠요', '급해요',
            '하나요', '하나요?', '하나요.', '하나요!',
            '하심', '하시나요', '하시나요?', '하시나요.',
            '요청', '요청하심', '요청합니다', '부탁합니다',
            
            # 질문 접미사
            '어떻게', '어떻게요', '어떻게 하나요', '어떻게 하나요?',
            '어디서', '어디서요', '어디서 하나요', '어디서 하나요?',
            '언제', '언제요', '언제 하나요', '언제 하나요?',
            '왜', '왜요', '왜 안되나요', '왜 안되나요?',
            
            # 기타 의미 없는 단어들
            '입니다', '입니다.', '입니다!', '입니다?',
            '있습니다', '있습니다.', '있습니다!', '있습니다?',
            '없습니다', '없습니다.', '없습니다!', '없습니다?',
            '됩니다', '됩니다.', '됩니다!', '됩니다?',
            '안됩니다', '안됩니다.', '안됩니다!', '안됩니다?',
            
            # 문장 끝 처리
            '...', '..', '.', '!', '?', '~', '~!', '~?'
        ]
        
        # 제외할 단어들 (너무 일반적인 단어들)
        self.exclude_words = {
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', '은', '는',
            '있', '없', '하', '되', '되다', '하다', '알', '모르', '보', '보기', '보고', '보면', '보니',
            '문의', '요청', '드립니다', '합니다', '됩니다', '있습니다', '없습니다',
            '어떻게', '무엇', '언제', '어디', '왜', '어떤', '몇', '얼마', '어느', '무슨',
            '문제', '해결', '방법', '설정', '관리', '확인', '체크', '검색', '조회'
        }
    
    def clean_text(self, text: str) -> str:
        """텍스트를 정리하고 조사와 접미사를 제거합니다."""
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 접미사 제거 (긴 것부터 제거)
        suffixes_sorted = sorted(self.suffixes_to_remove, key=len, reverse=True)
        for suffix in suffixes_sorted:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()
                break  # 가장 긴 접미사 하나만 제거
        
        # 조사 제거
        words = text.split()
        cleaned_words = []
        for word in words:
            # 조사가 붙은 단어에서 조사 제거
            cleaned_word = word
            for particle in self.particles_to_remove:
                if word.endswith(particle):
                    cleaned_word = word[:-len(particle)]
                    break
            if cleaned_word:  # 빈 문자열이 아닌 경우만 추가
                cleaned_words.append(cleaned_word)
        
        return ' '.join(cleaned_words)
    
    def extract_core_patterns(self, text: str) -> list:
        """텍스트에서 핵심 기술 용어 기반 2-3단어 패턴을 추출합니다."""
        patterns = []
        
        # 텍스트 정리 및 접미사 제거
        cleaned_text = self.clean_text(text)
        
        # 단어 분리
        words = cleaned_text.split()
        
        # 핵심 기술 용어가 포함된 단어들의 인덱스 찾기
        technical_word_indices = []
        for i, word in enumerate(words):
            if any(keyword in word.lower() for keyword in self.technical_keywords):
                technical_word_indices.append(i)
        
        # 핵심 기술 용어가 포함된 2-3단어 조합 생성
        for i in range(len(words) - 1):
            # 2단어 조합 (최소 하나는 기술 용어)
            pattern_2 = f"{words[i]} {words[i+1]}"
            if self._is_valid_technical_pattern(pattern_2, [i, i+1], technical_word_indices):
                patterns.append(pattern_2)
            
            # 3단어 조합 (가능한 경우, 최소 하나는 기술 용어)
            if i < len(words) - 2:
                pattern_3 = f"{words[i]} {words[i+1]} {words[i+2]}"
                if self._is_valid_technical_pattern(pattern_3, [i, i+1, i+2], technical_word_indices):
                    patterns.append(pattern_3)
        
        return list(set(patterns))  # 중복 제거
    
    def _is_valid_technical_pattern(self, pattern: str, word_indices: list, technical_indices: list) -> bool:
        """기술 용어가 포함된 유효한 패턴인지 확인합니다."""
        # 기본 유효성 검사
        if not self._is_valid_pattern(pattern):
            return False
        
        # 최소 하나의 단어는 기술 용어여야 함
        has_technical_word = any(idx in technical_indices for idx in word_indices)
        if not has_technical_word:
            return False
        
        return True
    
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
        
        # 접미사가 포함된 패턴 제외
        for suffix in self.suffixes_to_remove:
            if suffix in pattern:
                return False
        
        return True

async def test_improved_extraction():
    """개선된 패턴 추출 테스트"""
    try:
        db = await get_database()
        extractor = ImprovedPatternExtractor()
        
        print("=== 개선된 패턴 추출 테스트 ===")
        
        # 테스트 케이스들
        test_cases = [
            "포스 메인 재설치요",
            "클라우드에서 고객등록은 어느매뉴에서 어떻게 하나요?",
            "프로그램 재설치 요청 하심",
            "매출작업을 해놧는데 손님이 해당매출을 한개로 만들어달라고하는데 매출을 합칠수있나요?",
            "다시 결제가안된다고하십니다...",
            "자동로그인이 안됩니다.",
            "비즈메카 해당 업체 비즈메카에 해지 신청서 냈다고 함.",
            "디포 납품업체인데 프로그램 로그인이 안되는데 로그인 정보가 틀리다고 나옵니다. 아이디 비번 확인해주세요",
            "클라우드에서 견적작업 방법 알려주세요",
            "손님 5~12월까지 매출내역을 받고싶으신데 어디서 확인가능한지 문"
        ]
        
        print("\n=== 패턴 추출 결과 ===")
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            # 정리된 텍스트 확인
            cleaned_text = extractor.clean_text(test_input)
            print(f"정리된 텍스트: '{cleaned_text}'")
            
            # 패턴 추출
            patterns = extractor.extract_core_patterns(test_input)
            print(f"추출된 패턴들 ({len(patterns)}개):")
            
            for pattern in patterns:
                print(f"  - {pattern}")
        
        # 실제 knowledge_base에서 테스트
        print(f"\n=== knowledge_base 실제 데이터 테스트 ===")
        
        # 랜덤 5개 질문 선택
        all_questions = await db.knowledge_base.find({}, {"question": 1}).to_list(length=None)
        random_questions = random.sample(all_questions, 5)
        
        for i, q_data in enumerate(random_questions, 1):
            question = q_data.get("question", "")
            print(f"\n--- 실제 질문 {i}: '{question}' ---")
            
            # 정리된 텍스트 확인
            cleaned_text = extractor.clean_text(question)
            print(f"정리된 텍스트: '{cleaned_text}'")
            
            # 패턴 추출
            patterns = extractor.extract_core_patterns(question)
            print(f"추출된 패턴들 ({len(patterns)}개):")
            
            for pattern in patterns:
                print(f"  - {pattern}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_extraction()) 
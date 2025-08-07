#!/usr/bin/env python3
"""
간단한 한국어 품사 분석기 (Simple Korean POS Analyzer)
Java JVM 없이 정규표현식과 사전 기반으로 한국어 문장을 분석합니다.
"""

import json
import logging
import re
from typing import List, Tuple, Dict, Set
from collections import defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleKoreanAnalyzer:
    """간단한 한국어 품사 분석기 (Java JVM 불필요)"""
    
    def __init__(self):
        """초기화 - 한국어 품사 사전 설정"""
        
        # 조사 (Josa) - 문장에서 제거
        self.particles = {
            '이', '가', '을', '를', '의', '에', '로', '으로', '와', '과', '도', '만', '부터', '까지',
            '에서', '에게', '한테', '께', '보다', '처럼', '같이', '만큼', '치고', '마저', '조차',
            '은', '는', '이야', '야', '이에요', '예요', '입니다', '니다', '어요', '아요'
        }
        
        # 어미 (Eomi) - 동사/형용사 어미 (더 정확한 패턴)
        self.endings = {
            # 기본 어미
            '습니다', '니다', '어요', '아요', '이에요', '예요', '입니다', '니다',
            '고', '며', '거나', '든지', '면서', '고서', '다가', '자마자',
            '면', '으면', '아도', '어도', '아야', '어야', '아서', '어서',
            '는데', '은데', '는데', '은데', '는데', '은데', '는데', '은데',
            
            # 동사 어미 (더 정확한 패턴)
            '하시기', '바랍니다', '뜹니다', '됩니다', '됩니다', '됩니다',
            '해놧는데', '만들어달라고하는데', '합칠수있나요', '하려는데', '사용하시기', '바랍니다', '뜹니다',
            '하려고', '하고', '하는', '하시', '하세요', '하시면', '하시는', '하시는지',
            '할', '한', '하는', '했', '해', '하', '되', '된', '되는', '될',
            '있', '없', '가', '오', '보', '주', '받', '먹', '마시', '알', '모르',
            '후', '후에', '후에는', '후에도', '후에도', '후에도', '후에도', '후에도',
            '라', '라서', '라도', '라면', '라도', '라도', '라도', '라도',
            '합', '합니', '합니다', '합시', '합시다', '합시', '합시', '합시',
            
            # 추가 동사 어미 패턴
            '놧는데', '놨는데', '놓았는데', '놓는데',  # 해놧는데, 해놨는데
            '달라고', '달라고하는데', '달라고하는데',  # 만들어달라고하는데
            '수있나요', '수있나', '수있어요',  # 합칠수있나요
            '려고', '려는데', '려고하는데',  # 하려고, 하려는데
            '시기', '시면', '시는', '시는지',  # 하시기, 하시면
            '세요', '세요', '세요',  # 하세요
            '어서', '아서', '어도', '아도',  # 해서, 해도
            '면', '으면', '면',  # 하면
            '고', '고', '고',  # 하고
            '는', '은', '는',  # 하는
            '할', '한', '했', '해', '하',  # 동사 기본형
            '되', '된', '되는', '될',  # 되다 동사
            '있', '없', '가', '오', '보', '주', '받', '먹', '마시', '알', '모르'  # 기타 동사
        }
        
        # 일반적인 단어들 (제외)
        self.common_words = {
            '안녕', '감사', '죄송', '네', '예', '아니', '그', '이', '저', '우리', '저희', '그것', '이것',
            '하다', '되다', '있다', '없다', '보다', '주다', '받다', '가다', '오다', '먹다', '마시다',
            '손님', '한개', '어디', '언제', '어떻게', '왜', '무엇', '누구', '어떤', '몇', '얼마',
            '상담사', '사람', '고객', '사용자', '관리자', '직원', '회사', '업체', '매장', '점포'
        }
        
        # 기술적 키워드 (technical)
        self.technical_keywords = {
            '포스', '설치', '설정', '로그인', '비밀번호', '계정', '사용자', '관리자',
            '데이터', '백업', '복원', '업데이트', '다운로드', '업로드', '동기화',
            '연결', '재연결', '오류', '에러', '문제', '해결', '수정', '변경',
            '매출', '매입', '재고', '품목', '상품', '거래', '결제', '환불',
            '세금', '계산서', '영수증', '발행', '취소', '수정', '삭제',
            '프린터', '바코드', '스캐너', '단말기', '카드', '현금', '카드단말기',
            '엑셀', '파일', '문서', '보고서', '통계', '분석', '출력', '인쇄',
            '클라우드', '백오피스', '초기설정', '문구', '대기', '확인', '변경',
            '작업', '매출작업', '해당매출', '세금계산서', '바코드프린터'
        }
        
        # 복합어 분리 패턴
        self.compound_patterns = {
            '매출작업': '매출 작업',
            '세금계산서': '세금 계산서',
            '카드단말기': '카드 단말기',
            '바코드프린터': '바코드 프린터',
            '초기설정': '초기 설정',
            '해당매출': '해당 매출',
            '로그인': '로그 인',
            '비밀번호': '비밀 번호',
            '업로드': '업 로드',
            '다운로드': '다운 로드'
        }
        
        logger.info("간단한 한국어 품사 분석기 초기화 완료")
    
    def clean_text(self, text: str) -> str:
        """
        텍스트를 정리합니다 (조사, 어미 제거).
        
        Args:
            text (str): 정리할 텍스트
            
        Returns:
            str: 정리된 텍스트
        """
        # 복합어 분리
        for compound, separated in self.compound_patterns.items():
            text = text.replace(compound, separated)
        
        # 조사 제거 (단어 경계 고려)
        for particle in self.particles:
            # 단어 끝에 붙은 조사만 제거
            text = re.sub(rf'\b(\w+){re.escape(particle)}\b', r'\1', text)
        
        # 어미 제거 (더 정확한 패턴 매칭)
        for ending in self.endings:
            # 단어 끝에 붙은 어미만 제거 (더 정확한 패턴)
            text = re.sub(rf'(\w+){re.escape(ending)}(?=\s|$)', r'\1', text)
        
        # 특별한 동사 어미 패턴 처리
        # "해놧는데" -> "해놓" (동사 어간만 남김)
        text = re.sub(r'해놧는데|해놨는데|해놓았는데', '해놓', text)
        text = re.sub(r'만들어달라고하는데', '만들어달라', text)
        text = re.sub(r'합칠수있나요|합칠수있나|합칠수있어요', '합칠수있', text)
        text = re.sub(r'하려는데|하려고하는데', '하려', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_nouns_only(self, text: str) -> List[str]:
        """
        문장에서 명사만 추출합니다 (조사, 어미 제거 후).
        
        Args:
            text (str): 분석할 문장
            
        Returns:
            List[str]: 추출된 명사 리스트
        """
        # 텍스트 정리
        cleaned_text = self.clean_text(text)
        
        # 단어 분리
        words = cleaned_text.split()
        
        # 명사로 보이는 단어들만 추출 (조사나 어미가 제거된 단어들)
        nouns = []
        for word in words:
            # 길이가 2글자 이상이고 일반적인 단어가 아닌 것
            if len(word) >= 2 and word not in self.common_words:
                # 조사나 어미가 붙지 않은 순수한 단어들
                if not any(particle in word for particle in self.particles):
                    if not any(ending in word for ending in self.endings):
                        # 특수문자나 숫자가 포함된 단어 제외
                        if re.match(r'^[가-힣]+$', word):
                            nouns.append(word)
        
        logger.debug(f"추출된 명사: {nouns}")
        return nouns
    
    def extract_technical_patterns(self, text: str) -> List[str]:
        """
        문장에서 기술적 패턴을 추출합니다 (단일 단어 제외).
        
        Args:
            text (str): 분석할 문장
            
        Returns:
            List[str]: 추출된 기술적 패턴 리스트 (2단어 이상만)
        """
        nouns = self.extract_nouns_only(text)
        
        # 기술적 키워드가 포함된 명사만 필터링
        technical_nouns = [noun for noun in nouns if noun in self.technical_keywords]
        
        # 2-3단어 조합 생성 (기술적 명사들로만) - 단일 단어 제외
        patterns = []
        for i in range(len(technical_nouns)):
            for j in range(i + 1, min(i + 3, len(technical_nouns) + 1)):
                pattern = ' '.join(technical_nouns[i:j])
                if len(pattern.split()) >= 2:  # 최소 2단어 조합만
                    patterns.append(pattern)
        
        logger.debug(f"추출된 기술적 패턴: {patterns}")
        return patterns
    
    def analyze_sentence(self, text: str) -> Dict[str, any]:
        """
        문장을 종합적으로 분석합니다.
        
        Args:
            text (str): 분석할 문장
            
        Returns:
            Dict[str, any]: 분석 결과
        """
        result = {
            'original': text,
            'cleaned': self.clean_text(text),
            'nouns': self.extract_nouns_only(text),
            'technical_patterns': self.extract_technical_patterns(text)
        }
        
        return result
    
    def analyze_knowledge_base(self, questions: List[str]) -> Dict[str, List[str]]:
        """
        knowledge_base의 질문들을 분석하여 패턴을 추출합니다.
        
        Args:
            questions (List[str]): 분석할 질문 리스트
            
        Returns:
            Dict[str, List[str]]: 분석 결과
        """
        results = {
            'technical_patterns': [],
            'noun_combinations': [],
            'cleaned_texts': []
        }
        
        for i, question in enumerate(questions):
            logger.info(f"질문 {i+1}/{len(questions)} 분석 중: {question[:50]}...")
            
            # 문장 분석
            analysis = self.analyze_sentence(question)
            
            # 기술적 패턴 추출
            results['technical_patterns'].extend(analysis['technical_patterns'])
            
            # 명사 조합 추출
            nouns = analysis['nouns']
            if len(nouns) >= 2:
                for j in range(len(nouns) - 1):
                    noun_combo = f"{nouns[j]} {nouns[j+1]}"
                    results['noun_combinations'].append(noun_combo)
            
            # 정리된 텍스트
            results['cleaned_texts'].append(analysis['cleaned'])
        
        # 중복 제거
        results['technical_patterns'] = list(set(results['technical_patterns']))
        results['noun_combinations'] = list(set(results['noun_combinations']))
        
        return results
    
    def save_analysis_results(self, results: Dict[str, List[str]], filename: str = "simple_korean_analysis.json"):
        """
        분석 결과를 JSON 파일로 저장합니다.
        
        Args:
            results (Dict[str, List[str]]): 분석 결과
            filename (str): 저장할 파일명
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"분석 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"파일 저장 중 오류 발생: {e}")


def test_simple_analyzer():
    """간단한 분석기 테스트"""
    print("=== 간단한 한국어 품사 분석기 테스트 ===")
    
    # 테스트 문장들
    test_sentences = [
        "매출작업을 해놧는데 손님이 해당매출을 한개로 만들어달라고하는데 매출을 합칠수있나요?",
        "클라우드(백오피스) 로그인 하려는데 초기설정후 사용하시기 바랍니다.라는 문구가 뜹니다.",
        "세금계산서 발행을하면 취소가능한지 어디에서 확인이 되는지 대기나,바꿀수있는게 있는지 문의",
        "포스와 카드단말기가 연결이 안되어 있어",
        "상담사와 연결해줘",
        "엑셀 파일을 업로드하려고 하는데 오류가 발생합니다",
        "바코드프린터 설정을 변경하고 싶습니다"
    ]
    
    analyzer = SimpleKoreanAnalyzer()
    
    for sentence in test_sentences:
        print(f"\n문장: {sentence}")
        
        # 종합 분석
        analysis = analyzer.analyze_sentence(sentence)
        
        print(f"정리된 텍스트: {analysis['cleaned']}")
        print(f"추출된 명사: {analysis['nouns']}")
        print(f"기술적 패턴: {analysis['technical_patterns']}")


if __name__ == "__main__":
    test_simple_analyzer() 
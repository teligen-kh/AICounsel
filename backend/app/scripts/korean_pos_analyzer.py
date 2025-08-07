#!/usr/bin/env python3
"""
한국어 품사 분석기 (Korean POS Analyzer)
KoNLPy를 사용하여 한국어 문장의 품사를 분석하고, 
문맥 패턴 추출에 필요한 명사 조합을 생성합니다.
"""

import json
import logging
from typing import List, Tuple, Dict, Set
from collections import defaultdict
import re

# KoNLPy 라이브러리 import
try:
    from konlpy.tag import Okt, Kkma
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("KoNLPy가 설치되지 않았습니다. 설치 중...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "konlpy"])

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KoreanPOSAnalyzer:
    """한국어 품사 분석기"""
    
    def __init__(self):
        """초기화 - KoNLPy 형태소 분석기 설정"""
        if not KONLPY_AVAILABLE:
            raise ImportError("KoNLPy 라이브러리를 사용할 수 없습니다.")
        
        # Okt (Open Korean Text) - 더 정확한 형태소 분석
        self.okt = Okt()
        
        # Kkma - 더 세밀한 품사 태깅
        self.kkma = Kkma()
        
        # 품사별 필터링 설정
        self.target_pos = {
            'Noun': '명사',
            'Verb': '동사', 
            'Adjective': '형용사',
            'Josa': '조사',
            'Eomi': '어미',
            'Exclamation': '감탄사'
        }
        
        # 제외할 일반적인 단어들
        self.common_words = {
            '이', '가', '을', '를', '의', '에', '로', '으로', '와', '과', '도', '만', '부터', '까지',
            '안녕', '감사', '죄송', '네', '예', '아니', '그', '이', '저', '우리', '저희', '그것', '이것',
            '하다', '되다', '있다', '없다', '되다', '하다', '보다', '보다', '주다', '받다'
        }
        
        # 기술적 키워드 (technical)
        self.technical_keywords = {
            '포스', '설치', '설정', '로그인', '비밀번호', '계정', '사용자', '관리자',
            '데이터', '백업', '복원', '업데이트', '다운로드', '업로드', '동기화',
            '연결', '재연결', '오류', '에러', '문제', '해결', '수정', '변경',
            '매출', '매입', '재고', '품목', '상품', '거래', '결제', '환불',
            '세금', '계산서', '영수증', '발행', '취소', '수정', '삭제',
            '프린터', '바코드', '스캐너', '단말기', '카드', '현금', '카드단말기',
            '엑셀', '파일', '문서', '보고서', '통계', '분석', '출력', '인쇄'
        }
        
        logger.info("한국어 품사 분석기 초기화 완료")
    
    def analyze_pos(self, text: str) -> List[Tuple[str, str]]:
        """
        문장의 품사를 분석합니다.
        
        Args:
            text (str): 분석할 문장
            
        Returns:
            List[Tuple[str, str]]: (단어, 품사) 튜플 리스트
        """
        try:
            # Okt로 형태소 분석
            pos_result = self.okt.pos(text, norm=True, stem=True)
            logger.debug(f"Okt 분석 결과: {pos_result}")
            
            # Kkma로 추가 분석 (더 세밀한 품사 태깅)
            kkma_result = self.kkma.pos(text)
            logger.debug(f"Kkma 분석 결과: {kkma_result}")
            
            return pos_result
            
        except Exception as e:
            logger.error(f"품사 분석 중 오류 발생: {e}")
            return []
    
    def extract_nouns(self, text: str) -> List[str]:
        """
        문장에서 명사만 추출합니다.
        
        Args:
            text (str): 분석할 문장
            
        Returns:
            List[str]: 추출된 명사 리스트
        """
        pos_result = self.analyze_pos(text)
        nouns = [word for word, pos in pos_result if pos == 'Noun']
        
        # 일반적인 단어 제외
        nouns = [noun for noun in nouns if noun not in self.common_words]
        
        logger.debug(f"추출된 명사: {nouns}")
        return nouns
    
    def extract_technical_patterns(self, text: str) -> List[str]:
        """
        문장에서 기술적 패턴을 추출합니다.
        
        Args:
            text (str): 분석할 문장
            
        Returns:
            List[str]: 추출된 기술적 패턴 리스트
        """
        pos_result = self.analyze_pos(text)
        
        # 명사와 형용사 추출
        meaningful_words = []
        for word, pos in pos_result:
            if pos in ['Noun', 'Adjective'] and word not in self.common_words:
                meaningful_words.append(word)
        
        # 2-3단어 조합 생성
        patterns = []
        for i in range(len(meaningful_words)):
            for j in range(i + 1, min(i + 3, len(meaningful_words) + 1)):
                pattern = ' '.join(meaningful_words[i:j])
                if len(pattern.split()) >= 2:  # 최소 2단어 조합
                    patterns.append(pattern)
        
        # 기술적 키워드가 포함된 패턴만 필터링
        technical_patterns = []
        for pattern in patterns:
            words = pattern.split()
            if any(word in self.technical_keywords for word in words):
                technical_patterns.append(pattern)
        
        logger.debug(f"추출된 기술적 패턴: {technical_patterns}")
        return technical_patterns
    
    def clean_text(self, text: str) -> str:
        """
        텍스트를 정리합니다 (조사, 어미 제거).
        
        Args:
            text (str): 정리할 텍스트
            
        Returns:
            str: 정리된 텍스트
        """
        pos_result = self.analyze_pos(text)
        
        # 명사, 형용사, 동사 어간만 추출
        cleaned_words = []
        for word, pos in pos_result:
            if pos in ['Noun', 'Adjective'] or (pos == 'Verb' and word not in self.common_words):
                cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
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
            
            # 기술적 패턴 추출
            tech_patterns = self.extract_technical_patterns(question)
            results['technical_patterns'].extend(tech_patterns)
            
            # 명사 조합 추출
            nouns = self.extract_nouns(question)
            if len(nouns) >= 2:
                for j in range(len(nouns) - 1):
                    noun_combo = f"{nouns[j]} {nouns[j+1]}"
                    results['noun_combinations'].append(noun_combo)
            
            # 정리된 텍스트
            cleaned = self.clean_text(question)
            results['cleaned_texts'].append(cleaned)
        
        # 중복 제거
        results['technical_patterns'] = list(set(results['technical_patterns']))
        results['noun_combinations'] = list(set(results['noun_combinations']))
        
        return results
    
    def save_analysis_results(self, results: Dict[str, List[str]], filename: str = "korean_pos_analysis.json"):
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


def test_pos_analyzer():
    """품사 분석기 테스트"""
    print("=== 한국어 품사 분석기 테스트 ===")
    
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
    
    analyzer = KoreanPOSAnalyzer()
    
    for sentence in test_sentences:
        print(f"\n문장: {sentence}")
        
        # 품사 분석
        pos_result = analyzer.analyze_pos(sentence)
        print(f"품사 분석: {pos_result}")
        
        # 명사 추출
        nouns = analyzer.extract_nouns(sentence)
        print(f"명사 추출: {nouns}")
        
        # 기술적 패턴 추출
        tech_patterns = analyzer.extract_technical_patterns(sentence)
        print(f"기술적 패턴: {tech_patterns}")
        
        # 정리된 텍스트
        cleaned = analyzer.clean_text(sentence)
        print(f"정리된 텍스트: {cleaned}")


if __name__ == "__main__":
    test_pos_analyzer() 
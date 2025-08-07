#!/usr/bin/env python3
"""
최종 패턴 추출기
조사/동사 제거, 일반 단어 무시, 2단어 조합, 전문성 판단
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

class FinalPatternExtractor:
    """최종 패턴 추출기"""
    
    def __init__(self):
        # 제거할 조사들
        self.particles = {
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', '은', '는',
            '부터', '까지', '마다', '나', '라도', '이나', '든지', '든가', '든', '이나', '이나', '이나'
        }
        
        # 제거할 동사들 (더 포괄적으로)
        self.verbs = {
            # 기본 동사
            '하다', '되다', '있다', '없다', '알다', '모르다', '보다', '보기', '보고', '보면', '보니',
            '하시다', '되시다', '있으시다', '없으시다', '알으시다', '모르시다', '보시다',
            
            # 동사 활용형
            '하고', '되고', '있고', '없고', '알고', '모르고', '보고',
            '하면', '되면', '있으면', '없으면', '알면', '모르면', '보면',
            '해서', '돼서', '있어서', '없어서', '알아서', '몰라서', '봐서',
            '해도', '돼도', '있어도', '없어도', '알아도', '몰라도', '봐도',
            '하나', '되나', '있나', '없나', '알나', '모르나', '보나',
            '하는', '되는', '있는', '없는', '아는', '모르는', '보는',
            '한', '된', '있던', '없던', '알던', '모르던', '보던',
            '할', '될', '있을', '없을', '알', '모를', '볼',
            
            # 추가 동사들
            '해놧는데', '만들어달라고하는데', '합칠수있', '취소가능한지', '확인이', '되는지',
            '바꿀수있는게', '있는지', '문의', '요청', '하심', '드립니다', '합니다',
            '알려주세요', '부탁해요', '해주세요', '하나요', '하시나요', '하시나요?',
            '어떻게', '어떻게요', '어떻게 하나요', '어디서', '어디서요', '어디서 하나요',
            '언제', '언제요', '언제 하나요', '왜', '왜요', '왜 안되나요',
            '입니다', '있습니다', '없습니다', '됩니다', '안됩니다', '안됨', '안되',
            '가능한지', '가능한', '가능', '수있나요', '수있', '수있는', '수있는지',
            '해주시', '해주', '해주세요', '해주시나요', '해주시나요?', '해주시나요.',
            '해주시나요!', '해주시나요~', '해주시나요~!', '해주시나요~?',
            '하려는데', '사용하시기', '바랍니다', '뜹니다', '뜨는', '뜨고', '뜨면',
            '하시기', '바라', '뜨', '하려', '하려고', '하려면', '하려는', '하려던',
            '사용하', '사용하시', '사용하시는', '사용하시던', '사용하시고', '사용하시면'
        }
        
        # 제거할 접미사들
        self.suffixes = {
            '요', '해주세요', '부탁해요', '하나요', '하심', '하시나요',
            '요청', '요청하심', '요청합니다', '부탁합니다',
            '어떻게', '어떻게요', '어떻게 하나요',
            '어디서', '어디서요', '어디서 하나요',
            '언제', '언제요', '언제 하나요',
            '왜', '왜요', '왜 안되나요',
            '입니다', '있습니다', '없습니다', '됩니다', '안됩니다',
            '...', '..', '.', '!', '?', '~', '~!', '~?'
        }
        
        # 일반적인 단어들 (1개는 무시 가능)
        self.common_words = {
            '그러면', '그런데', '그래서', '그리고', '또는', '또한', '또는', '또한',
            '오늘', '내일', '어제', '지금', '나중에', '이후', '이전', '앞으로',
            '여기', '저기', '거기', '어디', '어느', '어떤', '무슨', '몇',
            '손님', '고객', '사장님', '직원', '관리자', '사용자',
            '한개', '두개', '세개', '여러개', '많이', '적게', '조금',
            '빨리', '천천히', '바로', '곧', '즉시', '나중에',
            '다시', '또', '또한', '또는', '그리고', '하지만', '그런데',
            '확인', '체크', '검토', '검사', '점검', '살펴보기',
            '문의', '질문', '묻기', '알아보기', '궁금', '궁금해요'
        }
        
        # 전문적인 단어들 (technical 분류 기준)
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
            '세금계산서', '발행', '취소', '대기', '변경', '수정',
            
            # 기타 기술
            '원격', '접속', '권한', '보안', '클라우드', '엑셀', '엑셀변환', '직인숨김',
            
            # 쇼핑몰
            '쇼핑몰', '주문', '주문서', '조회', '검색'
        }
    
    def clean_text(self, text: str) -> str:
        """텍스트를 정리하고 조사, 동사, 접미사를 제거합니다."""
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 접미사 제거 (긴 것부터)
        suffixes_sorted = sorted(self.suffixes, key=len, reverse=True)
        for suffix in suffixes_sorted:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()
                break
        
        # 단어 분리
        words = text.split()
        cleaned_words = []
        
        for word in words:
            # 조사 제거
            cleaned_word = word
            for particle in self.particles:
                if word.endswith(particle):
                    cleaned_word = word[:-len(particle)]
                    break
            
            # 동사 제거 (정확한 매칭)
            is_verb = False
            for verb in self.verbs:
                if cleaned_word == verb or cleaned_word.endswith(verb):
                    is_verb = True
                    break
            
            # 동사가 아니고 빈 문자열이 아니고 의미 있는 단어만 추가
            if not is_verb and cleaned_word and len(cleaned_word) > 1:
                cleaned_words.append(cleaned_word)
        
        # 띄어쓰기 분리 (복합어 분리)
        final_words = []
        for word in cleaned_words:
            # 복합어 분리 규칙
            if '매출' in word and word != '매출':
                # 매출작업 -> 매출 작업
                if word.startswith('매출'):
                    final_words.append('매출')
                    remaining = word[2:]  # '작업'
                    if remaining:
                        final_words.append(remaining)
                elif word.endswith('매출'):
                    # 해당매출 -> 해당 매출
                    remaining = word[:-2]  # '해당'
                    if remaining:
                        final_words.append(remaining)
                    final_words.append('매출')
                else:
                    final_words.append(word)
            else:
                final_words.append(word)
        
        return ' '.join(final_words)
    
    def extract_patterns(self, text: str) -> list:
        """텍스트에서 2단어 조합 패턴을 추출하고 전문성을 판단합니다."""
        # 텍스트 정리
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        # 일반적인 단어 개수 확인
        common_word_count = sum(1 for word in words if word in self.common_words)
        
        # 2단어 조합 생성
        patterns = []
        for i in range(len(words) - 1):
            word1, word2 = words[i], words[i+1]
            
            # 일반적인 단어가 포함된 패턴은 제외
            if word1 in self.common_words or word2 in self.common_words:
                continue
            
            pattern = f"{word1} {word2}"
            
            # 전문성 판단
            technical_score = 0
            if any(keyword in word1.lower() for keyword in self.technical_keywords):
                technical_score += 1
            if any(keyword in word2.lower() for keyword in self.technical_keywords):
                technical_score += 1
            
            # 최소 하나는 전문적인 단어여야 함
            if technical_score >= 1:
                patterns.append({
                    'pattern': pattern,
                    'technical_score': technical_score
                })
        
        return patterns
    
    def analyze_text(self, text: str) -> dict:
        """텍스트를 분석하고 최종 패턴을 결정합니다."""
        print(f"\n=== 텍스트 분석: '{text}' ===")
        
        # 정리된 텍스트
        cleaned_text = self.clean_text(text)
        print(f"정리된 텍스트: '{cleaned_text}'")
        
        # 단어 분리
        words = cleaned_text.split()
        print(f"단어들: {words}")
        
        # 일반적인 단어 확인
        common_words = [word for word in words if word in self.common_words]
        print(f"일반적인 단어들: {common_words}")
        
        # 패턴 추출
        patterns = self.extract_patterns(text)
        
        print(f"\n추출된 패턴들:")
        final_patterns = []
        
        for pattern_data in patterns:
            pattern = pattern_data['pattern']
            technical_score = pattern_data['technical_score']
            
            # 전문성 판단
            if technical_score >= 1:
                print(f"✅ {pattern} -> technical (점수: {technical_score})")
                final_patterns.append(pattern)
            else:
                print(f"❌ {pattern} -> 일반적 (점수: {technical_score})")
        
        return {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'words': words,
            'common_words': common_words,
            'patterns': patterns,
            'final_patterns': final_patterns
        }

async def test_final_extractor():
    """최종 패턴 추출기 테스트"""
    try:
        extractor = FinalPatternExtractor()
        
        print("=== 최종 패턴 추출기 테스트 ===")
        
        # 테스트 케이스들
        test_cases = [
            "포스 메인 재설치요",
            "클라우드에서 고객등록은 어느매뉴에서 어떻게 하나요?",
            "프로그램 재설치 요청 하심",
            "매출작업을 해놧는데 손님이 해당매출을 한개로 만들어달라고하는데 매출을 합칠수있나요?",
            "세금계산서 발행을하면 취소가능한지 어디에서 확인이 되는지 대기나,바꿀수있는게 있는지 문의"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i} ---")
            result = extractor.analyze_text(test_input)
            
            print(f"\n최종 문맥 패턴: {result['final_patterns']}")
        
        # 실제 knowledge_base에서 테스트
        print(f"\n=== knowledge_base 실제 데이터 테스트 ===")
        
        db = await get_database()
        all_questions = await db.knowledge_base.find({}, {"question": 1}).to_list(length=None)
        random_questions = random.sample(all_questions, 3)
        
        for i, q_data in enumerate(random_questions, 1):
            question = q_data.get("question", "")
            print(f"\n--- 실제 질문 {i} ---")
            result = extractor.analyze_text(question)
            
            print(f"\n최종 문맥 패턴: {result['final_patterns']}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_final_extractor()) 
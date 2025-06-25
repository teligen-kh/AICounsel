#!/usr/bin/env python3
"""
키워드 추출 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re

def extract_keywords(text: str):
    """텍스트에서 키워드를 추출합니다."""
    try:
        # 특수문자 제거 및 소문자 변환
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        words = text.split()
        
        # 불용어 목록 (더 구체적으로) - '방법' 제거
        stop_words = {
            '어떻게', '해요', '돼요', '있어요', '하나요', '오류', '발생', '했어요', '안돼요',
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', 
            '은', '는', '그', '저', '어떤', '무엇', '왜', '언제', '어디서', '잘', '못', '안',
            '문제', '해결', '알려', '주세요', '요청', '문의', '도움', '좀', '요',
            '아니', '그게', '아니라', '그것도', '방법이긴', '한데', '다른', '매장', '점주에게',
            '들으니', '하드디스크', '용량만큼', '사용이', '가능하게', '늘려주는', '방법이',
            '있다고', '하던데', '뭔소리야', '인가', '뭔가를', '늘리는', '방법이', '있다며'
        }
        
        # 불용어 제거 및 2글자 이상만 선택
        keywords = [word for word in words if word not in stop_words and len(word) >= 2]
        
        # 핵심 키워드 우선순위 부여
        priority_keywords = ['DB', '데이터베이스', '공간', '늘리기', '늘리', '방법', 'ARUMLOCADB', 'TABLE']
        filtered_keywords = []
        
        for keyword in keywords:
            if keyword in priority_keywords:
                filtered_keywords.insert(0, keyword)  # 우선순위 키워드를 앞에 배치
            else:
                filtered_keywords.append(keyword)
        
        return filtered_keywords[:5]  # 상위 5개만 반환
        
    except Exception as e:
        print(f"Error extracting keywords: {str(e)}")
        return []

def test_keywords():
    """키워드 추출 테스트"""
    print("=" * 60)
    print("키워드 추출 테스트")
    print("=" * 60)
    
    test_queries = [
        "DB 늘리기 방법",
        "데이터베이스 공간 늘리는 방법",
        "ARUMLOCADB TABLE 늘리기",
        "SQL Server Management Studio 설치",
        "포스 프로그램 오류"
    ]
    
    for query in test_queries:
        keywords = extract_keywords(query)
        print(f"질문: {query}")
        print(f"키워드: {keywords}")
        print("-" * 40)

if __name__ == "__main__":
    test_keywords() 
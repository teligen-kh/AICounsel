#!/usr/bin/env python3
"""
context_aware_classifier 패턴 매칭 로직 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database
from app.services.context_aware_classifier import ContextAwareClassifier

async def test_pattern_matching():
    """패턴 매칭 로직 테스트"""
    try:
        db = await get_database()
        classifier = ContextAwareClassifier(db)
        
        print("=== context_aware_classifier 패턴 매칭 테스트 ===")
        
        # 테스트 케이스들
        test_cases = [
            "상품엑셀 저장이 안됩니다",
            "바코드프린터 새로 구매했어요 설치요청 드립니다",
            "쇼핑몰을 저희가 확인하는 방법?",
            "안녕하세요?",
            "상담사 연결해주세요",
            "포스 연결 오류가 발생했습니다",
            "출하단가 1번에 올리는 방법 알려주세요",
            "직인숨김으로 엑셀변환시 공급자 칸까지 없어짐"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            # 분류 실행
            input_type, details = await classifier.classify_input(test_input)
            
            print(f"분류 결과: {input_type.value}")
            print(f"분류 이유: {details.get('reason', 'N/A')}")
            print(f"매칭된 단어: {details.get('matched_words', [])}")
            print(f"분류 소스: {details.get('source', 'N/A')}")
            
            # 패턴 매칭이 되었는지 확인
            if details.get('source') == 'context_patterns':
                print(f"✅ 패턴 매칭 성공!")
                print(f"   매칭율: {details.get('match_ratio', 'N/A')}")
                print(f"   패턴 ID: {details.get('pattern_id', 'N/A')}")
            else:
                print(f"❌ 패턴 매칭 실패 - {details.get('source', 'unknown')} 사용")
        
        # context_patterns 테이블 현황 확인
        print(f"\n=== context_patterns 테이블 현황 ===")
        patterns = await db.context_patterns.find({}).to_list(length=None)
        print(f"총 패턴 개수: {len(patterns)}")
        
        # 테스트 케이스와 관련된 패턴들 확인
        print(f"\n=== 관련 패턴 확인 ===")
        for test_input in test_cases:
            print(f"\n'{test_input}' 관련 패턴:")
            input_lower = test_input.lower()
            matching_patterns = []
            
            for pattern in patterns:
                pattern_text = pattern.get('pattern', '').lower()
                if pattern_text in input_lower or input_lower in pattern_text:
                    matching_patterns.append(pattern)
            
            if matching_patterns:
                for pattern in matching_patterns[:3]:  # 상위 3개만
                    print(f"  - {pattern['pattern']} -> {pattern['context']}")
            else:
                print("  - 매칭되는 패턴 없음")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pattern_matching()) 
#!/usr/bin/env python3
"""
Context Patterns 테스트 스크립트
"""

import sys
import os
import asyncio

# 현재 스크립트의 경로를 기준으로 상위 디렉토리들을 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.context_aware_classifier import ContextAwareClassifier

async def test_context_patterns():
    """Context Patterns 테스트"""
    print("=== Context Patterns 테스트 ===")
    
    # DB 연결
    db = await get_database()
    
    # context_patterns 테이블 확인
    patterns = list(db.context_patterns.find().limit(10))
    print(f"\n📊 Context Patterns 샘플 (총 {db.context_patterns.count_documents({})}개):")
    for pattern in patterns:
        print(f"  - {pattern['pattern']} -> {pattern['context']}")
    
    # ContextAwareClassifier 테스트
    classifier = ContextAwareClassifier(db)
    
    # 테스트 문장들
    test_sentences = [
        "매출작업을 해놧는데 손님이 해당매출을 한개로 만들어달라고하는데 매출을 합칠수있나요?",
        "클라우드(백오피스) 로그인 하려는데 초기설정후 사용하시기 바랍니다.라는 문구가 뜹니다.",
        "세금계산서 발행을하면 취소가능한지 어디에서 확인이 되는지 대기나,바꿀수있는게 있는지 문의",
        "포스와 카드단말기가 연결이 안되어 있어",
        "상담사와 연결해줘",
        "엑셀 파일을 업로드하려고 하는데 오류가 발생합니다",
        "바코드프린터 설정을 변경하고 싶습니다",
        "안녕하세요",
        "AI구나. 상담사 연결"
    ]
    
    print(f"\n🔍 분류 테스트:")
    for sentence in test_sentences:
        result = await classifier.classify_input(sentence)
        print(f"  '{sentence}' -> {result}")

if __name__ == "__main__":
    asyncio.run(test_context_patterns()) 
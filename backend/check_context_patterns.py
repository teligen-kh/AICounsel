#!/usr/bin/env python3
"""
context_patterns 테이블 확인 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database

async def check_context_patterns():
    """context_patterns 테이블의 내용을 확인합니다."""
    try:
        db = await get_database()
        
        # context_patterns 컬렉션에서 데이터 조회
        patterns = await db.context_patterns.find({}).to_list(length=None)
        
        print(f"=== context_patterns 테이블 현황 ===")
        print(f"총 패턴 개수: {len(patterns)}")
        print()
        
        if len(patterns) == 0:
            print("❌ context_patterns 테이블이 비어있습니다!")
            print("generate_context_patterns_fast.py를 실행해서 패턴을 생성해야 합니다.")
            return
        
        # 상위 10개 패턴 출력
        print("=== 상위 10개 패턴 ===")
        for i, pattern in enumerate(patterns[:10], 1):
            pattern_text = pattern.get('pattern', '')[:100]
            context = pattern.get('context', '')
            priority = pattern.get('priority', 0)
            print(f"{i}. 패턴: {pattern_text}...")
            print(f"   문맥: {context}")
            print(f"   우선순위: {priority}")
            print()
        
        # 문맥별 통계
        context_stats = {}
        for pattern in patterns:
            context = pattern.get('context', 'unknown')
            context_stats[context] = context_stats.get(context, 0) + 1
        
        print("=== 문맥별 통계 ===")
        for context, count in sorted(context_stats.items()):
            print(f"{context}: {count}개")
        
        # 특정 키워드 검색
        test_keywords = ['출하단가', '엑셀', '직인숨김', '공급자']
        print()
        print("=== 특정 키워드 검색 ===")
        for keyword in test_keywords:
            matching_patterns = []
            for pattern in patterns:
                if keyword in pattern.get('pattern', ''):
                    matching_patterns.append(pattern)
            
            print(f"'{keyword}' 포함 패턴: {len(matching_patterns)}개")
            for pattern in matching_patterns[:3]:  # 상위 3개만
                print(f"  - {pattern.get('pattern', '')[:50]}... -> {pattern.get('context', '')}")
            print()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_context_patterns()) 
#!/usr/bin/env python3
"""
테스트용 핵심 문맥 패턴들을 context_patterns에 추가
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database

async def add_test_patterns():
    """테스트용 핵심 문맥 패턴들을 추가합니다."""
    try:
        db = await get_database()
        
        print("=== 테스트용 핵심 문맥 패턴 추가 ===")
        
        # 테스트용 핵심 패턴들 (2-3단어 조합)
        test_patterns = [
            # 상품 관련
            {"pattern": "상품 엑셀", "context": "technical", "description": "상품 엑셀 관련 기술적 질문"},
            {"pattern": "상품 저장", "context": "technical", "description": "상품 저장 관련 기술적 질문"},
            {"pattern": "상품 업로드", "context": "technical", "description": "상품 업로드 관련 기술적 질문"},
            
            # 프린터 관련
            {"pattern": "바코드프린터", "context": "technical", "description": "바코드프린터 관련 기술적 질문"},
            {"pattern": "바코드 프린터", "context": "technical", "description": "바코드 프린터 관련 기술적 질문"},
            {"pattern": "영수증 프린터", "context": "technical", "description": "영수증 프린터 관련 기술적 질문"},
            
            # 출하단가 관련
            {"pattern": "출하단가", "context": "technical", "description": "출하단가 관련 기술적 질문"},
            {"pattern": "출하 단가", "context": "technical", "description": "출하 단가 관련 기술적 질문"},
            {"pattern": "단가 1번", "context": "technical", "description": "단가 1번 관련 기술적 질문"},
            
            # 직인 관련
            {"pattern": "직인숨김", "context": "technical", "description": "직인숨김 관련 기술적 질문"},
            {"pattern": "직인 숨김", "context": "technical", "description": "직인 숨김 관련 기술적 질문"},
            {"pattern": "엑셀변환", "context": "technical", "description": "엑셀변환 관련 기술적 질문"},
            {"pattern": "엑셀 변환", "context": "technical", "description": "엑셀 변환 관련 기술적 질문"},
            
            # 쇼핑몰 관련
            {"pattern": "쇼핑몰 확인", "context": "technical", "description": "쇼핑몰 확인 관련 기술적 질문"},
            {"pattern": "쇼핑몰 주문", "context": "technical", "description": "쇼핑몰 주문 관련 기술적 질문"},
            
            # 포스 관련
            {"pattern": "포스 연결", "context": "technical", "description": "포스 연결 관련 기술적 질문"},
            {"pattern": "포스 오류", "context": "technical", "description": "포스 오류 관련 기술적 질문"},
            
            # 상담사 관련 (casual)
            {"pattern": "상담사 연결", "context": "casual", "description": "상담사 연결 요청"},
            {"pattern": "사람 연결", "context": "casual", "description": "사람 연결 요청"},
            {"pattern": "대화 연결", "context": "casual", "description": "대화 연결 요청"},
        ]
        
        added_count = 0
        skipped_count = 0
        
        for pattern_data in test_patterns:
            pattern = pattern_data["pattern"]
            context = pattern_data["context"]
            description = pattern_data["description"]
            
            # 중복 체크
            existing = await db.context_patterns.find_one({"pattern": pattern})
            if existing:
                print(f"⏭️  이미 존재: {pattern} -> {context}")
                skipped_count += 1
                continue
            
            # 패턴 추가
            pattern_doc = {
                "pattern": pattern,
                "context": context,
                "description": description,
                "is_active": True,
                "accuracy": 0.95,  # 테스트용이므로 높은 정확도
                "usage_count": 0,
                "priority": 1,  # 높은 우선순위
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "source": "test_patterns"
            }
            
            await db.context_patterns.insert_one(pattern_doc)
            print(f"✅ 추가됨: {pattern} -> {context}")
            added_count += 1
        
        print(f"\n=== 추가 완료 ===")
        print(f"새로 추가된 패턴: {added_count}개")
        print(f"이미 존재하는 패턴: {skipped_count}개")
        
        # 전체 패턴 개수 확인
        total_count = await db.context_patterns.count_documents({})
        print(f"총 패턴 개수: {total_count}개")
        
        # 추가된 패턴들 확인
        print(f"\n=== 추가된 패턴들 ===")
        new_patterns = await db.context_patterns.find({"source": "test_patterns"}).to_list(length=None)
        for pattern in new_patterns:
            print(f"- {pattern['pattern']} -> {pattern['context']}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_test_patterns()) 
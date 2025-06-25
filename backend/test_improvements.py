#!/usr/bin/env python3
"""
개선된 기능들을 테스트하는 스크립트
- DB 답변 LLM 개선
- 줄바꿈 가독성
- 정확한 키워드 매칭
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.mongodb_search_service import MongoDBSearchService
from app.services.llm_service import LLMService
from app.database import connect_to_mongo, get_database
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_keyword_extraction():
    """키워드 추출 테스트"""
    print("=" * 60)
    print("키워드 추출 테스트")
    print("=" * 60)
    
    # MongoDB 연결
    await connect_to_mongo()
    db = await get_database()
    search_service = MongoDBSearchService(db)
    
    # 테스트 쿼리들
    test_queries = [
        "DB 공간을 늘리고 싶어요",
        "데이터베이스 늘리기 방법",
        "ARUMLOCADB 공간 늘리기",
        "DB 용량 늘리는 방법",
        "데이터베이스 크기 늘리기",
        "포스 설치 방법",
        "키오스크 오류 해결"
    ]
    
    for query in test_queries:
        print(f"\n질문: {query}")
        
        # 기본 키워드 추출
        basic_keywords = search_service._extract_keywords(query)
        print(f"기본 키워드: {basic_keywords}")
        
        # 개선된 키워드 추출
        improved_keywords = search_service._extract_improved_keywords(query)
        print(f"개선된 키워드: {improved_keywords}")
        
        # 검색 테스트
        answer = await search_service.search_answer(query)
        if answer:
            print(f"검색 결과: {answer[:100]}...")
        else:
            print("검색 결과: 없음")

async def test_llm_enhancement():
    """LLM 개선 테스트"""
    print("\n" + "=" * 60)
    print("LLM 개선 테스트")
    print("=" * 60)
    
    # MongoDB 연결
    await connect_to_mongo()
    db = await get_database()
    llm_service = LLMService(db, use_db_priority=True)
    
    # 테스트 케이스
    test_cases = [
        {
            "message": "DB 공간을 늘리고 싶어요",
            "db_answer": "ARUMLOCADB 테이블 공간 늘리기: 1. SQL Server Management Studio 실행 2. 데이터베이스 우클릭 3. 속성 선택 4. 파일 그룹에서 공간 증가"
        },
        {
            "message": "데이터베이스 용량 늘리기",
            "db_answer": "TABLE 크기 증가 방법: ALTER DATABASE 명령어 사용하여 데이터 파일 크기 확장"
        }
    ]
    
    for case in test_cases:
        print(f"\n질문: {case['message']}")
        print(f"DB 답변: {case['db_answer']}")
        
        try:
            enhanced_answer = await llm_service._enhance_db_answer_with_llm(
                case['message'], case['db_answer']
            )
            print(f"개선된 답변: {enhanced_answer}")
        except Exception as e:
            print(f"LLM 개선 오류: {str(e)}")
            # 포맷팅만 적용
            formatted_answer = llm_service._format_db_answer(case['db_answer'])
            print(f"포맷팅된 답변: {formatted_answer}")

async def test_formatting():
    """포맷팅 테스트"""
    print("\n" + "=" * 60)
    print("포맷팅 테스트")
    print("=" * 60)
    
    llm_service = LLMService()
    
    # 테스트 응답들
    test_responses = [
        "1. SQL Server Management Studio 실행 2. 데이터베이스 우클릭 3. 속성 선택 4. 파일 그룹에서 공간 증가",
        "ARUMLOCADB 테이블 공간 늘리기 방법입니다. 먼저 SQL Server Management Studio를 실행하세요. 그 다음 데이터베이스를 우클릭하고 속성을 선택합니다. 마지막으로 파일 그룹에서 공간을 증가시킵니다.",
        "DB 공간 늘리기: * SQL 실행 * 데이터베이스 선택 * 속성 변경 * 공간 증가"
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n테스트 {i}:")
        print(f"원본: {response}")
        formatted = llm_service._format_response(response)
        print(f"포맷팅: {formatted}")

async def main():
    """메인 테스트 함수"""
    try:
        await test_keyword_extraction()
        await test_formatting()
        await test_llm_enhancement()
        
        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
강화된 모듈 테스트 스크립트
제안하신 개선 방안을 구현한 모듈들을 종합적으로 테스트합니다.

테스트 대상:
1. 강화된 입력 분류기 (키워드 + LLM 의도 분석)
2. 하이브리드 응답 생성기 (DB + LLM 조합)
3. 강화된 채팅 서비스 (통합 시스템)
4. 모듈 전환 기능
5. 성능 비교 분석
"""

import sys
import os
import asyncio
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database
from app.services.enhanced_input_classifier import get_enhanced_input_classifier, EnhancedInputType
from app.services.hybrid_response_generator import get_hybrid_response_generator
from app.services.enhanced_chat_service import get_enhanced_chat_service
from app.config import enable_module, disable_module, print_module_status

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_enhanced_input_classifier():
    """강화된 입력 분류기 테스트"""
    print("\n=== 강화된 입력 분류기 테스트 ===")
    
    classifier = get_enhanced_input_classifier()
    
    test_cases = [
        # 인사/일상
        ("안녕하세요", "인사"),
        ("바쁘시죠?", "일상 대화"),
        ("AI는 사람인가요?", "AI 관련 질문"),
        
        # 전문 상담
        ("포스 설치가 어려워요", "전문 상담"),
        ("설정 방법 알려주세요", "전문 상담"),
        ("오류가 발생했어요", "전문 상담"),
        
        # 비상담
        ("한국의 수도는?", "비상담"),
        ("독도는 어디에 있나요?", "비상담"),
        ("정치에 대해 어떻게 생각하세요?", "비상담"),
        
        # 욕설
        ("바보같은 시스템이네", "욕설"),
        ("이런 멍청한 프로그램", "욕설"),
    ]
    
    for message, expected_type in test_cases:
        print(f"\n테스트: '{message}' (예상: {expected_type})")
        
        try:
            input_type, info = await classifier.classify_input(message)
            print(f"  결과: {input_type.value}")
            print(f"  방법: {info.get('classification_method', 'unknown')}")
            print(f"  키워드: {info.get('keywords', [])[:3]}")
            
            # 템플릿 응답 테스트
            if input_type in [EnhancedInputType.PROFANITY, EnhancedInputType.NON_COUNSELING]:
                template = classifier.get_response_template(input_type)
                print(f"  템플릿: {template[:50]}...")
                
        except Exception as e:
            print(f"  오류: {str(e)}")

async def test_hybrid_response_generator():
    """하이브리드 응답 생성기 테스트"""
    print("\n=== 하이브리드 응답 생성기 테스트 ===")
    
    db = await get_database()
    generator = get_hybrid_response_generator(db)
    
    test_cases = [
        ("포스 설치 방법", "전문 상담 - DB 검색"),
        ("안녕하세요", "일상 대화 - LLM 응답"),
        ("존재하지 않는 질문입니다", "DB 없음 - 상담사 연결"),
    ]
    
    for message, description in test_cases:
        print(f"\n테스트: '{message}' ({description})")
        
        try:
            response, info = await generator.generate_response(message)
            print(f"  응답: {response[:100]}...")
            print(f"  타입: {info.get('response_type', 'unknown')}")
            print(f"  DB 소스: {info.get('db_source', 'unknown')}")
            print(f"  LLM 사용: {info.get('llm_used', False)}")
            
        except Exception as e:
            print(f"  오류: {str(e)}")

async def test_enhanced_chat_service():
    """강화된 채팅 서비스 테스트"""
    print("\n=== 강화된 채팅 서비스 테스트 ===")
    
    db = await get_database()
    service = get_enhanced_chat_service(db)
    
    test_cases = [
        ("안녕하세요", "인사/일상"),
        ("포스 설치가 어려워요", "전문 상담"),
        ("한국의 수도는?", "비상담"),
        ("바보같은 시스템", "욕설"),
    ]
    
    for message, description in test_cases:
        print(f"\n테스트: '{message}' ({description})")
        
        try:
            # 기본 응답
            response = await service.process_message(message)
            print(f"  응답: {response[:100]}...")
            
            # 상세 정보
            detailed = await service.process_message_detailed(message)
            print(f"  분류: {detailed.get('input_type', 'unknown')}")
            print(f"  처리 시간: {detailed.get('processing_time_ms', 0):.2f}ms")
            
        except Exception as e:
            print(f"  오류: {str(e)}")

async def test_module_switching():
    """모듈 전환 테스트"""
    print("\n=== 모듈 전환 테스트 ===")
    
    print("현재 모듈 상태:")
    print_module_status()
    
    # 강화된 모듈 활성화
    print("\n강화된 모듈 활성화...")
    enable_module("enhanced_classification")
    enable_module("hybrid_response")
    
    print("활성화 후 모듈 상태:")
    print_module_status()
    
    # 기존 모듈 비활성화
    print("\n기존 모듈 비활성화...")
    disable_module("input_filtering")
    disable_module("conversation_analysis")
    
    print("비활성화 후 모듈 상태:")
    print_module_status()
    
    # 모든 모듈 초기화
    print("\n모든 모듈 초기화...")
    enable_module("mongodb_search")
    enable_module("llm_model")
    enable_module("conversation_analysis")
    enable_module("response_formatting")
    enable_module("input_filtering")
    disable_module("enhanced_classification")
    disable_module("hybrid_response")
    
    print("초기화 후 모듈 상태:")
    print_module_status()

async def test_performance_comparison():
    """성능 비교 테스트"""
    print("\n=== 성능 비교 테스트 ===")
    
    db = await get_database()
    
    # 기존 서비스
    from app.services.chat_service import ChatService
    from app.services.llm_service import LLMService
    
    llm_service = LLMService()
    old_service = ChatService(db, llm_service)
    
    # 강화된 서비스
    enhanced_service = get_enhanced_chat_service(db)
    
    test_message = "포스 설치가 어려워요"
    
    print(f"테스트 메시지: '{test_message}'")
    
    # 기존 서비스 테스트
    print("\n기존 서비스 테스트:")
    start_time = asyncio.get_event_loop().time()
    try:
        old_response = await old_service.process_message(test_message)
        old_time = (asyncio.get_event_loop().time() - start_time) * 1000
        print(f"  응답: {old_response[:50]}...")
        print(f"  시간: {old_time:.2f}ms")
    except Exception as e:
        print(f"  오류: {str(e)}")
    
    # 강화된 서비스 테스트
    print("\n강화된 서비스 테스트:")
    start_time = asyncio.get_event_loop().time()
    try:
        enhanced_response = await enhanced_service.process_message(test_message)
        enhanced_time = (asyncio.get_event_loop().time() - start_time) * 1000
        print(f"  응답: {enhanced_response[:50]}...")
        print(f"  시간: {enhanced_time:.2f}ms")
    except Exception as e:
        print(f"  오류: {str(e)}")

async def main():
    """메인 테스트 함수"""
    print("🤖 강화된 모듈 테스트 시작")
    print("제안하신 개선 방안을 구현한 모듈들을 테스트합니다.\n")
    
    try:
        # 1. 강화된 입력 분류기 테스트
        await test_enhanced_input_classifier()
        
        # 2. 하이브리드 응답 생성기 테스트
        await test_hybrid_response_generator()
        
        # 3. 강화된 채팅 서비스 테스트
        await test_enhanced_chat_service()
        
        # 4. 모듈 전환 테스트
        await test_module_switching()
        
        # 5. 성능 비교 테스트
        await test_performance_comparison()
        
        print("\n🎉 모든 테스트가 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
모듈 제어 사용 예제
코드 한 두 줄로 모듈을 제어하는 방법을 보여주는 교육용 스크립트

예제 시나리오:
1. 순수 LLM 모드 (MongoDB 검색 비활성화)
2. DB 우선 모드 (MongoDB 검색 우선)
3. 전체 분석 모드 (모든 모듈 활성화)
4. 테스트 모드 (최소 기능)
5. 사용자 정의 모드 (선택적 모듈 활성화)

실제 사용 시 참고용으로 활용하세요.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import enable_module, disable_module, get_module_status, print_module_status

def example_1_pure_llm_mode():
    """예제 1: 순수 LLM 모드 (MongoDB 검색 비활성화)"""
    print("=== 예제 1: 순수 LLM 모드 ===")
    
    # MongoDB 검색 모듈 비활성화
    disable_module("mongodb_search")
    
    # 고객 질문 분석 모듈 비활성화
    disable_module("conversation_analysis")
    
    print("✅ 순수 LLM 모드로 설정되었습니다.")
    print("   - MongoDB 검색 없이 LLM만 사용")
    print("   - 고객 질문 분석 없이 기본 응답")
    print_module_status()

def example_2_db_priority_mode():
    """예제 2: DB 우선 모드"""
    print("\n=== 예제 2: DB 우선 모드 ===")
    
    # MongoDB 검색 모듈 활성화
    enable_module("mongodb_search")
    
    # DB 우선 모드 활성화
    enable_module("db_priority")
    
    print("✅ DB 우선 모드로 설정되었습니다.")
    print("   - MongoDB에서 먼저 검색")
    print("   - DB에 없으면 LLM 사용")
    print_module_status()

def example_3_full_analysis_mode():
    """예제 3: 전체 분석 모드"""
    print("\n=== 예제 3: 전체 분석 모드 ===")
    
    # 모든 모듈 활성화
    enable_module("mongodb_search")
    enable_module("llm_model")
    enable_module("conversation_analysis")
    enable_module("response_formatting")
    enable_module("input_filtering")
    
    # DB 우선 모드 비활성화
    disable_module("db_priority")
    
    print("✅ 전체 분석 모드로 설정되었습니다.")
    print("   - 모든 모듈 활성화")
    print("   - 고객 질문 분석 후 적절한 응답")
    print_module_status()

def example_4_testing_mode():
    """예제 4: 테스트 모드 (최소 기능)"""
    print("\n=== 예제 4: 테스트 모드 ===")
    
    # LLM 모델만 활성화
    enable_module("llm_model")
    
    # 나머지 모듈 비활성화
    disable_module("mongodb_search")
    disable_module("conversation_analysis")
    disable_module("response_formatting")
    disable_module("input_filtering")
    disable_module("db_priority")
    
    print("✅ 테스트 모드로 설정되었습니다.")
    print("   - LLM 모델만 사용")
    print("   - 최소한의 기능으로 테스트")
    print_module_status()

def example_5_custom_mode():
    """예제 5: 사용자 정의 모드"""
    print("\n=== 예제 5: 사용자 정의 모드 ===")
    
    # 원하는 모듈만 활성화
    enable_module("llm_model")           # LLM 모델
    enable_module("conversation_analysis")  # 고객 질문 분석
    enable_module("response_formatting")    # 응답 포맷팅
    
    # 원하지 않는 모듈 비활성화
    disable_module("mongodb_search")     # MongoDB 검색 비활성화
    disable_module("input_filtering")    # 입력 필터링 비활성화
    disable_module("db_priority")        # DB 우선 모드 비활성화
    
    print("✅ 사용자 정의 모드로 설정되었습니다.")
    print("   - LLM + 분석 + 포맷팅만 사용")
    print("   - MongoDB 검색과 입력 필터링 비활성화")
    print_module_status()

def main():
    """메인 함수"""
    print("🤖 AICounsel 모듈 제어 예제")
    print("코드 한 두 줄로 모듈을 제어할 수 있습니다!\n")
    
    # 현재 상태 확인
    print("현재 모듈 상태:")
    print_module_status()
    
    # 예제 실행
    example_1_pure_llm_mode()
    example_2_db_priority_mode()
    example_3_full_analysis_mode()
    example_4_testing_mode()
    example_5_custom_mode()
    
    print("\n🎉 모든 예제가 완료되었습니다!")
    print("\n실제 사용 시에는 다음과 같이 사용하세요:")
    print("  from app.config import enable_module, disable_module")
    print("  enable_module('mongodb_search')    # MongoDB 검색 활성화")
    print("  disable_module('input_filtering')  # 입력 필터링 비활성화")

if __name__ == "__main__":
    main() 
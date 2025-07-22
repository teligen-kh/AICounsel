#!/usr/bin/env python3
"""
모듈 제어 스크립트
코드 한 두 줄로 모듈을 활성화/비활성화할 수 있는 명령줄 도구

사용법:
- python module_control.py enable <모듈명>
- python module_control.py disable <모듈명>
- python module_control.py status
- python module_control.py reset

지원 모듈:
- mongodb_search: MongoDB 검색 모듈
- llm_model: LLM 모델 연동 모듈
- conversation_analysis: 고객 질문 분석 모듈
- response_formatting: 응답 포맷팅 모듈
- input_filtering: 입력 필터링 모듈
- enhanced_classification: 강화된 입력 분류 모듈
- hybrid_response: 하이브리드 응답 생성 모듈
- db_priority: DB 우선 모드
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import enable_module, disable_module, get_module_status, print_module_status

def main():
    """메인 함수"""
    if len(sys.argv) < 3:
        print("사용법:")
        print("  python module_control.py enable <모듈명>")
        print("  python module_control.py disable <모듈명>")
        print("  python module_control.py status")
        print("  python module_control.py reset")
        print("\n사용 가능한 모듈:")
        print("  - mongodb_search: MongoDB 검색 모듈")
        print("  - llm_model: LLM 모델 연동 모듈")
        print("  - conversation_analysis: 고객 질문 분석 모듈")
        print("  - response_formatting: 응답 포맷팅 모듈")
        print("  - input_filtering: 입력 필터링 모듈")
        print("  - db_priority: DB 우선 모드")
        return
    
    action = sys.argv[1].lower()
    
    if action == "status":
        print_module_status()
        return
    
    elif action == "reset":
        print("모든 모듈을 기본 상태로 초기화합니다...")
        enable_module("mongodb_search")
        enable_module("llm_model")
        enable_module("conversation_analysis")
        enable_module("response_formatting")
        enable_module("input_filtering")
        print("✅ 모든 모듈이 기본 상태로 초기화되었습니다.")
        print_module_status()
        return
    
    elif len(sys.argv) < 3:
        print("❌ 모듈명을 지정해주세요.")
        return
    
    module_name = sys.argv[2].lower()
    
    try:
        if action == "enable":
            enable_module(module_name)
            print(f"✅ {module_name} 모듈이 활성화되었습니다.")
        elif action == "disable":
            disable_module(module_name)
            print(f"❌ {module_name} 모듈이 비활성화되었습니다.")
        else:
            print("❌ 잘못된 액션입니다. 'enable' 또는 'disable'을 사용하세요.")
            return
        
        print_module_status()
        
    except ValueError as e:
        print(f"❌ 오류: {str(e)}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    main() 
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.input_filter import get_input_filter, InputType

def test_input_filter():
    """입력 필터 테스트"""
    
    input_filter = get_input_filter()
    
    # 테스트 메시지들
    test_messages = [
        "안녕하세요?",
        "바쁘시죠? 점심인데 식사는 하셨어요?",
        "너는 AI야?",
        "한국에 대해서 설명해줘",
        "독도는 어느 나라 땅이야?",
        "핸드스캐너가 작동이 안되는데 어떻게 해야 해?",
        "이 바보같은 AI야",
        "포스 프로그램 설치 방법 알려줘"
    ]
    
    print("=== 입력 필터 테스트 ===\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"--- 테스트 {i} ---")
        print(f"질문: {message}")
        
        # 입력 분류
        input_type, details = input_filter.classify_input(message)
        print(f"분류: {input_type.value}")
        print(f"이유: {details['reason']}")
        
        # 템플릿 응답
        template_response = input_filter.get_response_template(input_type, "텔리젠")
        print(f"템플릿 응답: {template_response}")
        print()
    
    print("=== 테스트 완료 ===")

if __name__ == "__main__":
    test_input_filter() 
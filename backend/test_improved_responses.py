import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_style_manager import get_style_manager, ConversationStyle
from app.services.llama_cpp_processor import LlamaCppProcessor
from app.services.input_filter import get_input_filter, InputType

def test_improved_responses():
    """개선된 응답 테스트"""
    
    # 모델 경로 설정
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_path = os.path.join(base_path, "Phi-3.5-mini-instruct-Q8_0.gguf")
    
    if not os.path.exists(model_path):
        print("❌ 모델 파일을 찾을 수 없습니다!")
        return
    
    # 테스트 메시지들
    test_messages = [
        "안녕하세요?",
        "바쁘시죠? 점심인데 식사는 하셨어요?",
        "너는 AI야?",
        "한국에 대해서 설명해줘",
        "독도는 어느 나라 땅이야?",
        "핸드스캐너가 작동이 안되는데 어떻게 해야 해?",
        "이 바보같은 AI야",
        "포스 프로그램 설치 방법 알려줘",
        "요즘 날씨가 어때?",
        "한강 작가가 쓴 소설 제목 알려줘",
        "너는 사람이야?",
        "그냥 대화하고 싶어",
        "재미있게 이야기해줘"
    ]
    
    # 친근한 스타일로 테스트
    style = ConversationStyle.FRIENDLY
    style_manager = get_style_manager()
    input_filter = get_input_filter()
    
    print(f"=== {style_manager.get_style(style)['name']} 스타일 테스트 ===\n")
    print(f"업체명: {style_manager.company_name}")
    print(f"시스템 프롬프트: {style_manager.get_system_prompt(style)}")
    print(f"파라미터: {style_manager.get_parameters(style)}")
    print()
    
    try:
        # 프로세서 초기화
        processor = LlamaCppProcessor(model_path, "phi-3.5-mini-instruct", style)
        
        for i, message in enumerate(test_messages, 1):
            print(f"--- 테스트 {i} ---")
            print(f"질문: {message}")
            
            # 입력 분류 테스트
            input_type, details = input_filter.classify_input(message)
            print(f"입력 분류: {input_type.value} - {details['reason']}")
            
            # 입력 처리 (필터링)
            template_response, use_template = processor.process_user_input(message)
            
            if use_template:
                # 템플릿 응답 사용
                response = template_response
                print(f"템플릿 응답 사용")
            else:
                # LLM 처리
                prompt = processor.create_casual_prompt(message)
                response = processor.generate_response(prompt)
                print(f"LLM 응답 생성")
            
            print(f"답변: {response}")
            print(f"답변 길이: {len(response)} 문자")
            print()
        
        # 리소스 정리
        processor.cleanup()
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
    
    print("=== 테스트 완료 ===")

if __name__ == "__main__":
    test_improved_responses() 
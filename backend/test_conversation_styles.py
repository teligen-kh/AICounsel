import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_style_manager import get_style_manager, ConversationStyle
from app.services.llama_cpp_processor import LlamaCppProcessor

def test_conversation_styles():
    """다양한 대화 스타일 테스트"""
    
    # 모델 경로 설정
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_path = os.path.join(base_path, "Phi-3.5-mini-instruct-Q8_0.gguf")
    
    if not os.path.exists(model_path):
        print("❌ 모델 파일을 찾을 수 없습니다!")
        return
    
    # 테스트 메시지
    test_message = "바쁘시죠? 점심인데 식사는 하셨어요?"
    
    # 스타일 매니저 가져오기
    style_manager = get_style_manager()
    
    print("=== 대화 스타일 테스트 시작 ===\n")
    
    # 각 스타일별로 테스트
    for style in ConversationStyle:
        print(f"--- {style_manager.get_style(style)['name']} 스타일 테스트 ---")
        
        try:
            # 프로세서 초기화
            processor = LlamaCppProcessor(model_path, "phi-3.5-mini-instruct", style)
            
            # 프롬프트 생성
            prompt = processor.create_casual_prompt(test_message)
            
            # 응답 생성
            response = processor.generate_response(prompt)
            
            print(f"질문: {test_message}")
            print(f"답변: {response}")
            print(f"스타일: {style.value}")
            print(f"파라미터: {processor.get_optimized_parameters()}")
            print()
            
            # 리소스 정리
            processor.cleanup()
            
        except Exception as e:
            print(f"❌ {style.value} 스타일 테스트 실패: {str(e)}\n")
    
    print("=== 테스트 완료 ===")

if __name__ == "__main__":
    test_conversation_styles() 
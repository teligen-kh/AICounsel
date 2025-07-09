import os
import sys
import logging
from llama_cpp import Llama

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_phi35_model():
    """Phi-3.5 모델 기본 테스트"""
    
    # 모델 경로 설정
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_path = os.path.join(base_path, "Phi-3.5-mini-instruct-Q8_0.gguf")
    
    print(f"모델 경로: {model_path}")
    print(f"모델 파일 존재: {os.path.exists(model_path)}")
    
    if not os.path.exists(model_path):
        print("❌ 모델 파일을 찾을 수 없습니다!")
        return False
    
    try:
        print("🔄 Phi-3.5 모델 로딩 중...")
        
        # llama-cpp 모델 초기화
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,           # 컨텍스트 길이
            n_threads=8,          # CPU 스레드 수
            n_gpu_layers=0,       # CPU 모드
            verbose=False,        # 로그 최소화
            seed=42              # 재현 가능성
        )
        
        print("✅ Phi-3.5 모델 로딩 성공!")
        
        # 테스트 프롬프트들
        test_prompts = [
            "안녕하세요",
            "오늘 날씨가 어때요?",
            "한국어로 대화해주세요",
            "간단한 인사말을 해주세요"
        ]
        
        print("\n=== Phi-3.5 모델 테스트 시작 ===")
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n--- 테스트 {i}: {prompt} ---")
            
            try:
                # Phi-3.5 기본 프롬프트 형식 사용
                formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
                
                print(f"프롬프트: {formatted_prompt}")
                
                # 응답 생성
                response = llm(
                    formatted_prompt,
                    max_tokens=100,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=50,
                    repeat_penalty=1.1,
                    stop=["<|user|>", "<|end|>"]
                )
                
                generated_text = response.get('choices', [{}])[0].get('text', '').strip()
                print(f"응답: {generated_text}")
                
            except Exception as e:
                print(f"❌ 테스트 {i} 실패: {str(e)}")
        
        print("\n=== 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"❌ 모델 로딩 실패: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_phi35_model()
    if success:
        print("\n🎉 Phi-3.5 모델 테스트 성공!")
    else:
        print("\n💥 Phi-3.5 모델 테스트 실패!") 
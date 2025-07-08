#!/usr/bin/env python3
"""
LLaMA 2 7B Chat 모델 기본 테스트
"""

import os
import sys
import time
from llama_cpp import Llama

def test_llama_basic():
    """LLaMA 2 7B 모델 기본 테스트"""
    
    # 모델 경로
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "llama-2-7b-chat.Q4_K_M.gguf")
    
    if not os.path.exists(model_path):
        print(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
        return False
    
    print(f"✅ 모델 파일 발견: {model_path}")
    
    try:
        # 모델 초기화
        print("🔄 모델 초기화 중...")
        start_time = time.time()
        
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=8,
            n_gpu_layers=0,
            verbose=False,
            seed=42
        )
        
        init_time = time.time() - start_time
        print(f"✅ 모델 초기화 완료: {init_time:.2f}초")
        
        # 테스트 케이스들
        test_cases = [
            ("안녕하세요", "한국어로 답변해주세요."),
            ("오늘 날씨가 좋네요", "한국어로 답변해주세요."),
            ("한국어로 대화해주세요", ""),
            ("1+1은 몇인가요?", "한국어로 답변해주세요."),
            ("인공지능에 대해 설명해주세요", "한국어로 답변해주세요.")
        ]
        
        print("\n" + "="*50)
        print("LLaMA 2 7B Chat 모델 테스트 시작")
        print("="*50)
        
        for i, (test_input, instruction) in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i}: {test_input} ---")
            
            # 프롬프트 생성 (한국어 응답 유도)
            if instruction:
                prompt = f"<s>[INST] {test_input} {instruction} [/INST]"
            else:
                prompt = f"<s>[INST] {test_input} [/INST]"
            print(f"프롬프트: {prompt}")
            
            # 응답 생성
            start_time = time.time()
            
            response = llm(
                prompt,
                max_tokens=100,
                temperature=0.6,
                top_p=0.9,
                top_k=50,
                repeat_penalty=1.1,
                stop=["[INST]", "</s>"]
            )
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # ms
            
            # 응답 추출
            generated_text = response.get('choices', [{}])[0].get('text', '').strip()
            
            print(f"응답: {generated_text}")
            print(f"처리 시간: {processing_time:.2f}ms")
            print(f"응답 길이: {len(generated_text)} 문자")
            
            # 응답 품질 평가
            if len(generated_text) < 5:
                print("⚠️  응답이 너무 짧음")
            elif processing_time > 10000:  # 10초
                print("⚠️  처리 시간이 너무 김")
            elif not any(char in generated_text for char in ['안녕', '네', '좋', '감사', '도움', '설명', '답변']):
                print("⚠️  응답이 부적절함")
            else:
                print("✅ 응답 품질 양호")
        
        print("\n" + "="*50)
        print("테스트 완료")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llama_basic()
    if success:
        print("\n✅ LLaMA 2 7B 모델 테스트 성공")
    else:
        print("\n❌ LLaMA 2 7B 모델 테스트 실패")
        sys.exit(1) 
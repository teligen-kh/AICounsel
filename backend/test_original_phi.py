#!/usr/bin/env python3
"""
원본 Phi-3.5-mini-instruct 모델의 한국어 응답 능력 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_original_phi_korean():
    """원본 Phi-3.5-mini-instruct 모델의 한국어 응답 테스트"""
    
    print("=" * 60)
    print("원본 Phi-3.5-mini-instruct 모델 한국어 응답 테스트")
    print("=" * 60)
    
    try:
        # 로컬 모델 경로 설정
        print("1. 로컬 모델 로딩 중...")
        model_path = "finetune_tool/models/microsoft/Phi-3.5-mini-instruct"
        
        if not os.path.exists(model_path):
            print(f"❌ 모델 경로를 찾을 수 없습니다: {model_path}")
            return
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        print("✅ 로컬 모델 로딩 완료")
        
        # 한국어 테스트 프롬프트들
        test_prompts = [
            "안녕하세요, 오늘 날씨가 어때요?",
            "한국어로 대화할 수 있나요?",
            "상담사로서 고객의 스트레스를 어떻게 도와줄 수 있을까요?",
            "직장에서 동료와 갈등이 있을 때 어떻게 해결하면 좋을까요?",
            "가족과의 관계가 어려울 때 어떤 방법으로 접근하면 좋을까요?"
        ]
        
        print("\n2. 한국어 응답 테스트 시작...")
        print("-" * 40)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n테스트 {i}: {prompt}")
            print("-" * 30)
            
            # 프롬프트 포맷팅
            formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
            
            # 토크나이징
            inputs = tokenizer(formatted_prompt, return_tensors="pt")
            
            # 생성
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # 응답 디코딩
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 사용자 프롬프트 제거하고 어시스턴트 응답만 추출
            if "<|assistant|>" in response:
                assistant_response = response.split("<|assistant|>")[-1].strip()
            else:
                assistant_response = response.replace(formatted_prompt, "").strip()
            
            print(f"응답: {assistant_response}")
            
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        logging.error(f"테스트 중 오류: {str(e)}")

if __name__ == "__main__":
    test_original_phi_korean() 
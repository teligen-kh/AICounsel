#!/usr/bin/env python3
"""
Polyglot-Ko 5.8B 간단 테스트 (텍스트 완성 방식)
"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_simple_completion():
    """간단한 텍스트 완성 테스트"""
    
    # 모델 경로
    model_path = os.path.join(project_root.parent, "models", "Polyglot-Ko-5.8B")
    
    if not os.path.exists(model_path):
        logging.error(f"모델 경로가 존재하지 않습니다: {model_path}")
        return False
    
    try:
        logging.info("=== Polyglot-Ko 간단 텍스트 완성 테스트 ===")
        
        # 토크나이저 로딩
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 모델 로딩
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # 테스트 케이스들 (텍스트 완성 방식)
        test_cases = [
            "안녕하세요",
            "반갑습니다",
            "도움이 필요합니다",
            "오늘 날씨가 좋네요",
            "한국어로 자기소개를 해주세요"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logging.info(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            # 텍스트 완성 프롬프트
            prompt = f"{test_input} "
            logging.info(f"프롬프트: '{prompt}'")
            
            # 입력 인코딩
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=64)
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            
            # 매우 보수적인 생성 파라미터
            generation_params = {
                "max_new_tokens": 10,      # 매우 짧게
                "temperature": 0.01,       # 거의 결정적
                "top_p": 0.99,            # 높게
                "do_sample": True,
                "repetition_penalty": 1.0,
                "num_beams": 1,
                "use_cache": True
            }
            
            # 생성
            with torch.no_grad():
                outputs = model.generate(**inputs, **generation_params)
            
            # 응답 디코딩
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = generated_text[len(prompt):].strip()
            
            logging.info(f"생성된 텍스트: '{generated_text}'")
            logging.info(f"응답: '{response}'")
            
            # 노이즈 확인
            noise_keywords = ['맛집', '술집', '이자카야', 'Neoalpha', '토론', 'KST']
            found_noise = [kw for kw in noise_keywords if kw in response]
            if found_noise:
                logging.warning(f"노이즈 발견: {found_noise}")
            else:
                logging.info("✅ 노이즈 없음")
        
        return True
        
    except Exception as e:
        logging.error(f"테스트 중 오류: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_completion()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
새로 다운로드한 Polyglot-Ko 5.8B 모델 기본 테스트
아무 조정 없이 순수한 모델 상태로 테스트
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_polyglot_fresh():
    """새로 다운로드한 Polyglot-Ko 5.8B 기본 테스트"""
    
    # 모델 경로
    model_path = "D:/AICounsel/models/Polyglot-Ko-5.8B"
    
    try:
        logging.info("=== 새로 다운로드한 Polyglot-Ko 5.8B 기본 테스트 시작 ===")
        logging.info("아무 조정 없이 순수한 모델 상태로 테스트")
        
        # 1. 모델 로딩
        logging.info("모델 로딩 중...")
        start_time = time.time()
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        load_time = time.time() - start_time
        logging.info(f"모델 로딩 완료: {load_time:.2f}초")
        
        # 2. 토크나이저 설정 (기본값 그대로)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        logging.info("토크나이저 설정 완료")
        
        # 3. 기본 테스트 케이스들
        test_cases = [
            "안녕하세요",
            "오늘 날씨가 좋네요",
            "도움이 필요하신가요?",
            "감사합니다",
            "반갑습니다"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logging.info(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            # 입력 인코딩 (기본값 그대로)
            inputs = tokenizer(test_input, return_tensors="pt", padding=True, truncation=True, max_length=100)
            
            # 기본 생성 파라미터 (transformers 기본값)
            generation_params = {
                "max_new_tokens": 50,      # 기본값
                "temperature": 1.0,        # 기본값
                "top_p": 1.0,             # 기본값
                "do_sample": False,        # 기본값
                "num_beams": 1,           # 기본값
                "use_cache": True         # 기본값
            }
            
            # 생성
            start_gen = time.time()
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    **generation_params
                )
            gen_time = time.time() - start_gen
            
            # 응답 디코딩 (원본 그대로)
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = generated_text[len(test_input):].strip()
            
            logging.info(f"입력: '{test_input}'")
            logging.info(f"전체 출력: '{generated_text}'")
            logging.info(f"원본 응답: '{response}'")
            logging.info(f"생성 시간: {gen_time:.2f}초")
            logging.info(f"응답 길이: {len(response)}")
            
            # 응답 품질 평가
            if response and len(response) > 0:
                logging.info("✅ 응답 생성됨")
            else:
                logging.warning("❌ 빈 응답")
        
        logging.info("\n=== 기본 테스트 완료 ===")
        logging.info("이제 이 결과를 기준으로 우리 프로그램을 맞춰보겠습니다.")
        
    except Exception as e:
        logging.error(f"테스트 실패: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    test_polyglot_fresh() 
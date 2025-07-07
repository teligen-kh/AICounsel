#!/usr/bin/env python3
"""
Polyglot-Ko 5.8B 모델 기본 상태 테스트
모든 후처리/필터링 제거하고 원본 응답만 확인
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_polyglot_raw():
    """Polyglot-Ko 기본 상태 테스트 (모든 후처리 제거)"""
    
    # 모델 경로
    model_path = "D:/AICounsel/models/Polyglot-Ko-5.8B"
    
    try:
        logging.info("=== Polyglot-Ko 5.8B 기본 상태 테스트 시작 ===")
        logging.info("모든 후처리/필터링 제거, 원본 응답만 확인")
        
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
        
        # 2. 토크나이저 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        logging.info("토크나이저 설정 완료")
        
        # 3. 다양한 테스트 케이스들
        test_cases = [
            "안녕하세요",
            "오늘 날씨가 좋네요",
            "도움이 필요하신가요?",
            "상품 등록 방법 알려주세요",
            "감사합니다",
            "반갑습니다",
            "무엇을 도와드릴까요?"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logging.info(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            # 입력 인코딩 (token_type_ids 제거)
            inputs = tokenizer(test_input, return_tensors="pt", padding=True, truncation=True, max_length=50)
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            
            # 기본 생성 파라미터 (매우 단순)
            generation_params = {
                "max_new_tokens": 30,      # 적당한 길이
                "temperature": 0.7,        # 기본값
                "top_p": 0.9,             # 기본값
                "do_sample": True,
                "repetition_penalty": 1.0,
                "num_beams": 1,
                "use_cache": True
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
            
            # 노이즈 패턴 확인 (정보만)
            noise_patterns = [
                '맛집', '술집', '이자카야', '분위기좋', '소개해드리려고',
                'Neoalpha', '토론', 'KST', 'rqproduct', '머니투데이',
                '기자', '뉴스', 'http', 'www', '바로바로'
            ]
            
            found_noise = [pattern for pattern in noise_patterns if pattern in response]
            if found_noise:
                logging.warning(f"노이즈 패턴 발견: {found_noise}")
            else:
                logging.info("✅ 노이즈 패턴 없음")
            
            # 응답 품질 평가
            if response and len(response) > 0:
                logging.info("✅ 응답 생성됨")
            else:
                logging.warning("❌ 빈 응답")
        
        logging.info("\n=== 기본 상태 테스트 완료 ===")
        logging.info("이 결과를 기준으로 우리 프로그램을 맞춰보겠습니다.")
        
    except Exception as e:
        logging.error(f"테스트 실패: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    test_polyglot_raw() 
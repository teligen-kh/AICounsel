#!/usr/bin/env python3
"""
Polyglot-Ko 5.8B 모델 공식 사용법 테스트
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_polyglot_official():
    """Polyglot-Ko 모델의 공식 사용법을 테스트합니다."""
    
    model_path = "D:/AICounsel/models/Polyglot-Ko-5.8B"
    
    try:
        logger.info("=== Polyglot-Ko 공식 사용법 테스트 시작 ===")
        
        # 1. 토크나이저 로딩
        logger.info("1. 토크나이저 로딩...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # 토크나이저 정보 확인
        logger.info(f"BOS 토큰: {tokenizer.bos_token}")
        logger.info(f"EOS 토큰: {tokenizer.eos_token}")
        logger.info(f"PAD 토큰: {tokenizer.pad_token}")
        logger.info(f"UNK 토큰: {tokenizer.unk_token}")
        
        # PAD 토큰 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info(f"PAD 토큰을 EOS 토큰으로 설정: {tokenizer.pad_token}")
        
        # 2. 모델 로딩
        logger.info("2. 모델 로딩...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # 3. 공식 프롬프트 형식 테스트
        logger.info("3. 공식 프롬프트 형식 테스트...")
        
        # 테스트 메시지들
        test_messages = [
            "안녕하세요?",
            "오늘 날씨가 어때요?",
            "한국어를 잘하시네요!"
        ]
        
        for i, message in enumerate(test_messages, 1):
            logger.info(f"\n--- 테스트 {i}: {message} ---")
            
            # 공식 프롬프트 형식
            prompt = f"사용자: {message}\n어시스턴트:"
            logger.info(f"프롬프트: {prompt}")
            
            # 토크나이징
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            )
            logger.info(f"입력 토큰 수: {inputs.input_ids.shape[1]}")
            
            # 생성 시작
            start_time = time.time()
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=50,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    repetition_penalty=1.1,
                    num_beams=1,
                    use_cache=True
                )
            
            generation_time = time.time() - start_time
            
            # 응답 디코딩
            generated_tokens = outputs[0, inputs.input_ids.shape[1]:]
            response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            logger.info(f"생성 시간: {generation_time:.2f}초")
            logger.info(f"생성된 토큰 수: {len(generated_tokens)}")
            logger.info(f"응답: '{response}'")
            
            # 성능 분석
            tokens_per_second = len(generated_tokens) / generation_time
            logger.info(f"토큰당 처리 시간: {generation_time/len(generated_tokens)*1000:.2f}ms")
            logger.info(f"초당 토큰 수: {tokens_per_second:.2f}")
        
        logger.info("\n=== 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    test_polyglot_official() 
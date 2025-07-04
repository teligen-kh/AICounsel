#!/usr/bin/env python3
"""
Polyglot-Ko 5.8B 기본 응답 테스트 스크립트
가장 단순한 형태로 모델이 정상 작동하는지 확인
"""

import os
import sys
import logging
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_polyglot_basic.log', encoding='utf-8')
    ]
)

def test_basic_polyglot():
    """Polyglot-Ko 기본 테스트"""
    
    # 모델 경로 설정 (상위 디렉토리의 models 폴더)
    model_path = os.path.join(project_root.parent, "models", "Polyglot-Ko-5.8B")
    
    if not os.path.exists(model_path):
        logging.error(f"모델 경로가 존재하지 않습니다: {model_path}")
        return False
    
    try:
        logging.info("=== Polyglot-Ko 5.8B 기본 테스트 시작 ===")
        
        # 1. 토크나이저 로딩
        logging.info("토크나이저 로딩 중...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # 토크나이저 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        logging.info(f"✅ 토크나이저 로딩 완료 - vocab_size: {tokenizer.vocab_size}")
        
        # 2. 모델 로딩
        logging.info("모델 로딩 중...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        logging.info("✅ 모델 로딩 완료")
        
        # 3. 기본 테스트 케이스들
        test_cases = [
            "안녕하세요",
            "반갑습니다",
            "오늘 날씨가 좋네요",
            "도움이 필요합니다"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logging.info(f"\n=== 테스트 케이스 {i}: '{test_input}' ===")
            
            # 가장 단순한 프롬프트 (텍스트 완성)
            prompt = f"{test_input}"
            logging.info(f"프롬프트: '{prompt}'")
            
            # 입력 인코딩
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=128)
            # token_type_ids 제거 (Polyglot-Ko가 지원하지 않음)
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            logging.info(f"입력 토큰 수: {inputs['input_ids'].shape[1]}")
            
            # 기본 생성 파라미터 (매우 보수적)
            generation_params = {
                "max_new_tokens": 20,      # 매우 짧게
                "temperature": 0.1,        # 매우 낮게 (일관성)
                "top_p": 0.9,             # 높게 (다양성)
                "do_sample": True,
                "repetition_penalty": 1.0, # 기본값
                "num_beams": 1,
                "use_cache": True
            }
            
            logging.info(f"생성 파라미터: {generation_params}")
            
            # 생성
            start_time = time.time()
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    **generation_params
                )
            end_time = time.time()
            
            # 응답 디코딩
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logging.info(f"전체 생성 텍스트: '{generated_text}'")
            
            # 프롬프트 제거하여 실제 응답만 추출
            response = generated_text[len(prompt):].strip()
            logging.info(f"실제 응답: '{response}'")
            
            # 처리 시간
            processing_time = (end_time - start_time) * 1000
            logging.info(f"처리 시간: {processing_time:.2f}ms")
            
            # 응답 품질 평가
            if response:
                if len(response) >= 2:
                    logging.info("✅ 응답 생성 성공")
                else:
                    logging.warning("⚠️ 응답이 너무 짧음")
            else:
                logging.error("❌ 응답이 비어있음")
        
        # 4. 추가 테스트: 더 긴 응답
        logging.info("\n=== 긴 응답 테스트 ===")
        long_prompt = "한국어로 자기소개를 해주세요"
        logging.info(f"프롬프트: '{long_prompt}'")
        
        inputs = tokenizer(long_prompt, return_tensors="pt", padding=True, truncation=True, max_length=128)
        # token_type_ids 제거
        if 'token_type_ids' in inputs:
            del inputs['token_type_ids']
        
        generation_params = {
            "max_new_tokens": 50,      # 더 길게
            "temperature": 0.3,        # 조금 높게
            "top_p": 0.8,
            "do_sample": True,
            "repetition_penalty": 1.1,
            "num_beams": 1,
            "use_cache": True
        }
        
        with torch.no_grad():
            outputs = model.generate(**inputs, **generation_params)
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = generated_text[len(long_prompt):].strip()
        logging.info(f"긴 응답: '{response}'")
        
        logging.info("=== 기본 테스트 완료 ===")
        return True
        
    except Exception as e:
        logging.error(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")
        return False

def test_without_filtering():
    """후처리 필터링 없이 테스트"""
    logging.info("\n=== 후처리 필터링 없이 테스트 ===")
    
    # 기존 후처리 로직을 사용하지 않고 원본 응답 확인
    test_input = "안녕하세요"
    
    # 모델 경로 (상위 디렉토리의 models 폴더)
    model_path = os.path.join(project_root.parent, "models", "Polyglot-Ko-5.8B")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # 다양한 프롬프트 형식 테스트
        prompts = [
            test_input,  # 단순 텍스트
            f"{test_input}\n",  # 줄바꿈 추가
            f"사용자: {test_input}\n",  # 사용자 형식
            f"질문: {test_input}\n답변:",  # 질문-답변 형식
        ]
        
        for i, prompt in enumerate(prompts, 1):
            logging.info(f"\n--- 프롬프트 형식 {i}: '{prompt}' ---")
            
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=128)
            # token_type_ids 제거
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            
            generation_params = {
                "max_new_tokens": 30,
                "temperature": 0.2,
                "top_p": 0.9,
                "do_sample": True,
                "repetition_penalty": 1.0,
                "num_beams": 1,
                "use_cache": True
            }
            
            with torch.no_grad():
                outputs = model.generate(**inputs, **generation_params)
            
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = generated_text[len(prompt):].strip()
            
            logging.info(f"원본 응답: '{response}'")
            logging.info(f"응답 길이: {len(response)}")
            
            # 노이즈 패턴 확인
            noise_patterns = ['노라', '잖습니까', 'ㅎㅎ', '맛집', '위키피디아', '기사', '블로그']
            found_noise = [pattern for pattern in noise_patterns if pattern in response]
            if found_noise:
                logging.warning(f"노이즈 패턴 발견: {found_noise}")
            else:
                logging.info("✅ 노이즈 패턴 없음")
        
        return True
        
    except Exception as e:
        logging.error(f"필터링 없이 테스트 중 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    logging.info("Polyglot-Ko 5.8B 기본 응답 테스트 시작")
    
    # 1. 기본 테스트
    success1 = test_basic_polyglot()
    
    # 2. 필터링 없이 테스트
    success2 = test_without_filtering()
    
    if success1 and success2:
        logging.info("✅ 모든 테스트 완료")
        logging.info("결과를 확인하고 다음 단계를 결정하세요.")
    else:
        logging.error("❌ 일부 테스트 실패")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
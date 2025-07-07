#!/usr/bin/env python3
"""
llama-cpp-python으로 llama-2-7b-chat.Q4_K_M.gguf 모델 기본 테스트
"""

import time
import logging
from llama_cpp import Llama

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_llama_cpp_basic():
    """llama-cpp-python 기본 테스트"""
    
    # 모델 경로
    model_path = "D:/AICounsel/models/llama-2-7b-chat.Q4_K_M.gguf"
    
    try:
        logging.info("=== llama-cpp-python 기본 테스트 시작 ===")
        logging.info(f"모델: {model_path}")
        
        # 1. 모델 로딩
        logging.info("모델 로딩 중...")
        start_time = time.time()
        
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,  # 컨텍스트 길이
            n_threads=4,  # CPU 스레드 수
            n_gpu_layers=0,  # GPU 사용 안함 (CPU만)
            verbose=False
        )
        
        load_time = time.time() - start_time
        logging.info(f"모델 로딩 완료: {load_time:.2f}초")
        
        # 2. 기본 테스트 케이스들
        test_cases = [
            "안녕하세요",
            "오늘 날씨가 좋네요",
            "도움이 필요하신가요?",
            "감사합니다",
            "반갑습니다"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logging.info(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            # LLaMA 2 Chat 형식 프롬프트
            prompt = f"<s>[INST] {test_input} [/INST]"
            
            # 생성 파라미터
            generation_params = {
                "max_tokens": 100,      # 최대 토큰 수
                "temperature": 0.7,     # 온도
                "top_p": 0.9,          # top-p
                "stop": ["</s>", "[INST]"]  # 중단 토큰
            }
            
            # 생성
            start_gen = time.time()
            response = llm(
                prompt,
                **generation_params
            )
            gen_time = time.time() - start_gen
            
            # 응답 추출
            generated_text = response['choices'][0]['text'].strip()
            
            logging.info(f"입력: '{test_input}'")
            logging.info(f"프롬프트: '{prompt}'")
            logging.info(f"응답: '{generated_text}'")
            logging.info(f"생성 시간: {gen_time:.2f}초")
            logging.info(f"응답 길이: {len(generated_text)}")
            
            # 응답 품질 평가
            if generated_text and len(generated_text) > 0:
                logging.info("✅ 응답 생성됨")
            else:
                logging.warning("❌ 빈 응답")
        
        logging.info("\n=== llama-cpp-python 기본 테스트 완료 ===")
        
    except Exception as e:
        logging.error(f"테스트 실패: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    test_llama_cpp_basic() 
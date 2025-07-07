#!/usr/bin/env python3
"""
LLaMA 3.1 8B GGUF 모델 다운로드
"""

import os
import sys
from pathlib import Path
import logging
import requests
from tqdm import tqdm

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_file(url, filepath):
    """파일 다운로드 함수"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filepath, 'wb') as file, tqdm(
        desc=filepath.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            pbar.update(size)

def download_llama_gguf():
    """LLaMA 3.1 8B GGUF 모델 다운로드"""
    
    try:
        logging.info("=== LLaMA 3.1 8B GGUF 모델 다운로드 시작 ===")
        
        # 모델 경로 설정
        models_dir = Path("D:/AICounsel/models")
        model_filename = "llama-3.1-8b-instruct-Q4_K_M.gguf"
        model_path = models_dir / model_filename
        
        logging.info(f"다운로드 경로: {model_path}")
        
        # 기존 파일이 있으면 삭제
        if model_path.exists():
            logging.info("기존 GGUF 파일 삭제 중...")
            model_path.unlink()
            logging.info("기존 GGUF 파일 삭제 완료")
        
        # GGUF 모델 다운로드 URL (TheBloke의 양자화된 모델)
        # 실제 URL은 Hugging Face에서 확인 필요
        url = "https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q4_K_M.gguf"
        
        logging.info("LLaMA 3.1 8B GGUF 모델 다운로드 시작...")
        logging.info(f"다운로드 URL: {url}")
        logging.info("이 과정은 시간이 오래 걸릴 수 있습니다.")
        
        # 파일 다운로드
        download_file(url, model_path)
        
        logging.info("=== LLaMA 3.1 8B GGUF 모델 다운로드 완료 ===")
        logging.info(f"저장 위치: {model_path}")
        
        # 파일 크기 확인
        file_size = model_path.stat().st_size / (1024**3)  # GB
        logging.info(f"파일 크기: {file_size:.2f}GB")
        
        return True
        
    except Exception as e:
        logging.error(f"다운로드 실패: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = download_llama_gguf()
    if success:
        print("✅ 다운로드 성공!")
    else:
        print("❌ 다운로드 실패!")
        sys.exit(1) 
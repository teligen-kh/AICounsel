#!/usr/bin/env python3
"""
Polyglot-Ko 5.8B 모델 다운로드 스크립트
"""

import os
import sys
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import snapshot_download

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_polyglot_ko():
    """Polyglot-Ko 5.8B 모델을 다운로드합니다."""
    
    # 모델 정보
    model_name = "EleutherAI/polyglot-ko-5.8b"
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "Polyglot-Ko-5.8B")
    
    try:
        logger.info(f"Starting download of {model_name}")
        logger.info(f"Local path: {local_path}")
        
        # 디렉토리 생성
        os.makedirs(local_path, exist_ok=True)
        
        # 모델 다운로드
        logger.info("Downloading model files...")
        snapshot_download(
            repo_id=model_name,
            local_dir=local_path,
            local_dir_use_symlinks=False
        )
        
        logger.info("✅ Model downloaded successfully!")
        
        # 토크나이저 테스트
        logger.info("Testing tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(local_path)
        logger.info(f"Tokenizer loaded: {type(tokenizer).__name__}")
        
        # 모델 테스트 (CPU에서)
        logger.info("Testing model loading...")
        model = AutoModelForCausalLM.from_pretrained(
            local_path,
            torch_dtype="auto",
            device_map="cpu",
            trust_remote_code=True
        )
        logger.info(f"Model loaded: {type(model).__name__}")
        
        logger.info("✅ All tests passed!")
        logger.info(f"Model is ready to use at: {local_path}")
        
    except Exception as e:
        logger.error(f"Failed to download model: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_polyglot_ko() 
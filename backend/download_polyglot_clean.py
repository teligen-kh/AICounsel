#!/usr/bin/env python3
"""
Polyglot-Ko 5.8B 모델 새로 다운로드
"""

import os
import sys
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_polyglot_clean():
    """Polyglot-Ko 5.8B 모델 새로 다운로드"""
    
    try:
        logging.info("=== Polyglot-Ko 5.8B 모델 새로 다운로드 시작 ===")
        
        # 모델 경로 설정 (절대 경로)
        models_dir = Path("D:/AICounsel/models")
        model_path = models_dir / "Polyglot-Ko-5.8B"
        
        logging.info(f"다운로드 경로: {model_path}")
        
        # 기존 폴더가 남아있으면 삭제
        if model_path.exists():
            logging.info("기존 모델 폴더 삭제 중...")
            import shutil
            shutil.rmtree(model_path)
            logging.info("기존 모델 폴더 삭제 완료")
        
        # 모델 다운로드
        logging.info("Polyglot-Ko 5.8B 모델 다운로드 시작...")
        logging.info("이 과정은 시간이 오래 걸릴 수 있습니다.")
        
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        # 토크나이저 다운로드
        logging.info("토크나이저 다운로드 중...")
        tokenizer = AutoTokenizer.from_pretrained(
            "EleutherAI/polyglot-ko-5.8b",
            cache_dir=models_dir,
            trust_remote_code=True
        )
        logging.info("토크나이저 다운로드 완료")
        
        # 모델 다운로드
        logging.info("모델 다운로드 중... (약 11GB)")
        model = AutoModelForCausalLM.from_pretrained(
            "EleutherAI/polyglot-ko-5.8b",
            cache_dir=models_dir,
            torch_dtype="auto",
            trust_remote_code=True
        )
        logging.info("모델 다운로드 완료")
        
        # 모델 저장
        logging.info("모델을 로컬에 저장 중...")
        model.save_pretrained(model_path)
        tokenizer.save_pretrained(model_path)
        logging.info("모델 저장 완료")
        
        logging.info("=== Polyglot-Ko 5.8B 모델 다운로드 완료 ===")
        logging.info(f"저장 위치: {model_path}")
        
        return True
        
    except Exception as e:
        logging.error(f"다운로드 실패: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = download_polyglot_clean()
    if success:
        print("✅ 다운로드 성공!")
    else:
        print("❌ 다운로드 실패!")
        sys.exit(1) 
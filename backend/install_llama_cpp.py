#!/usr/bin/env python3
"""
llama-cpp-python 설치 및 GGUF 모델 다운로드 스크립트
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command: str, description: str) -> bool:
    """명령어 실행"""
    try:
        logging.info(f"실행 중: {description}")
        logging.info(f"명령어: {command}")
        
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logging.info(f"출력: {result.stdout}")
        
        logging.info(f"✅ {description} 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ {description} 실패: {e}")
        if e.stderr:
            logging.error(f"오류 출력: {e.stderr}")
        return False

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logging.error("Python 3.8 이상이 필요합니다.")
        return False
    
    logging.info(f"✅ Python 버전 확인: {version.major}.{version.minor}.{version.micro}")
    return True

def install_llama_cpp():
    """llama-cpp-python 설치"""
    commands = [
        ("pip install llama-cpp-python", "llama-cpp-python 설치"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def download_gguf_models():
    """GGUF 모델 다운로드"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # 다운로드할 모델 목록
    models = [
        {
            "name": "polyglot-ko-5.8b-Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/polyglot-ko-5.8B-GGUF/resolve/main/polyglot-ko-5.8b.Q4_K_M.gguf",
            "description": "Polyglot-Ko 5.8B GGUF 모델"
        },
        {
            "name": "llama-3.1-8b-instruct-Q4_K_M.gguf", 
            "url": "https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q4_K_M.gguf",
            "description": "LLaMA 3.1 8B Instruct GGUF 모델"
        }
    ]
    
    for model in models:
        model_path = models_dir / model["name"]
        
        if model_path.exists():
            logging.info(f"✅ {model['description']} 이미 존재: {model_path}")
            continue
        
        logging.info(f"다운로드 시작: {model['description']}")
        
        # wget 또는 curl 사용
        if run_command(f"wget -O {model_path} {model['url']}", f"{model['description']} 다운로드"):
            logging.info(f"✅ {model['description']} 다운로드 완료")
        elif run_command(f"curl -L -o {model_path} {model['url']}", f"{model['description']} 다운로드 (curl)"):
            logging.info(f"✅ {model['description']} 다운로드 완료")
        else:
            logging.error(f"❌ {model['description']} 다운로드 실패")
            return False
    
    return True

def create_env_file():
    """환경 변수 파일 생성"""
    env_content = """# LLM 설정
USE_LLAMA_CPP=true

# 모델 설정
DEFAULT_MODEL_TYPE=polyglot-ko-5.8b

# 성능 설정
LLAMA_CPP_N_THREADS=8
LLAMA_CPP_N_CTX=2048
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        logging.info("✅ .env 파일 생성 완료")
    else:
        logging.info("✅ .env 파일 이미 존재")

def main():
    """메인 함수"""
    logging.info("=== llama-cpp-python 설치 및 설정 시작 ===")
    
    # 1. Python 버전 확인
    if not check_python_version():
        return False
    
    # 2. llama-cpp-python 설치
    if not install_llama_cpp():
        return False
    
    # 3. GGUF 모델 다운로드
    if not download_gguf_models():
        return False
    
    # 4. 환경 변수 파일 생성
    create_env_file()
    
    logging.info("=== 설치 및 설정 완료 ===")
    logging.info("사용 방법:")
    logging.info("1. 환경 변수 설정: export USE_LLAMA_CPP=true")
    logging.info("2. 서버 실행: python -m uvicorn app.main:app --reload")
    logging.info("3. 테스트: curl -X POST http://localhost:8000/api/v1/chat/send -H 'Content-Type: application/json' -d '{\"message\": \"안녕하세요\"}'")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
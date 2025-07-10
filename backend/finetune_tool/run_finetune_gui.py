#!/usr/bin/env python3
"""
파인튜닝 GUI 실행 스크립트
GPU 컴퓨터에서 실행하여 파인튜닝을 진행
"""

import os
import sys
import subprocess
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """필요한 패키지 확인"""
    
    required_packages = [
        'torch',
        'transformers', 
        'peft',
        'accelerate',
        'bitsandbytes',
        'datasets',
        'customtkinter',
        'matplotlib',
        'seaborn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} 설치됨")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"✗ {package} 설치되지 않음")
    
    if missing_packages:
        logger.error(f"다음 패키지들이 설치되지 않았습니다: {missing_packages}")
        logger.info("다음 명령어로 설치하세요:")
        logger.info(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_gpu():
    """GPU 확인"""
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"✓ GPU 발견: {gpu_name}")
            logger.info(f"  GPU 개수: {gpu_count}")
            logger.info(f"  메모리: {gpu_memory:.1f}GB")
            
            return True
        else:
            logger.warning("GPU가 감지되지 않았습니다.")
            logger.warning("CPU에서 실행할 수 있지만 매우 느릴 수 있습니다.")
            return False
            
    except Exception as e:
        logger.error(f"GPU 확인 중 오류: {e}")
        return False

def install_requirements():
    """requirements.txt 설치"""
    
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if os.path.exists(requirements_file):
        logger.info("requirements.txt 설치 중...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ])
            logger.info("패키지 설치 완료")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"패키지 설치 실패: {e}")
            return False
    else:
        logger.warning("requirements.txt 파일을 찾을 수 없습니다.")
        return False

def run_gui():
    """GUI 실행"""
    
    try:
        from gui.main_window import FinetuneGUI
        
        logger.info("파인튜닝 GUI를 시작합니다...")
        
        app = FinetuneGUI()
        app.run()
        
    except ImportError as e:
        logger.error(f"GUI 모듈을 불러올 수 없습니다: {e}")
        logger.info("필요한 패키지가 설치되어 있는지 확인하세요.")
        return False
    except Exception as e:
        logger.error(f"GUI 실행 중 오류: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    
    logger.info("=== AI 상담사 파인튜닝 도구 ===")
    
    # 현재 디렉토리 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"작업 디렉토리: {current_dir}")
    
    # 의존성 확인
    logger.info("\n1. 의존성 확인 중...")
    if not check_dependencies():
        logger.info("\n패키지 설치를 시도합니다...")
        if not install_requirements():
            logger.error("패키지 설치에 실패했습니다. 수동으로 설치해주세요.")
            return 1
    
    # GPU 확인
    logger.info("\n2. GPU 확인 중...")
    check_gpu()
    
    # GUI 실행
    logger.info("\n3. GUI 시작 중...")
    if not run_gui():
        return 1
    
    logger.info("프로그램을 종료합니다.")
    return 0

if __name__ == "__main__":
    exit(main()) 
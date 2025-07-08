#!/usr/bin/env python3
"""
Phi-3.5 3.8B GGUF 모델 다운로드
"""

import os
import requests
import sys

def download_phi_3_5():
    """Phi-3.5 3.8B GGUF 모델 다운로드"""
    
    # 모델 정보
    model_url = "https://huggingface.co/TheBloke/Phi-3.5-3.8B-GGUF/resolve/main/phi-3.5-3.8b.Q4_K_M.gguf"
    model_name = "phi-3.5-3.8b.Q4_K_M.gguf"
    
    # 저장 경로
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_path = os.path.join(models_dir, model_name)
    
    # 디렉토리 생성
    os.makedirs(models_dir, exist_ok=True)
    
    print(f"🔄 Phi-3.5 3.8B GGUF 모델 다운로드 시작")
    print(f"📁 저장 경로: {model_path}")
    print(f"🌐 다운로드 URL: {model_url}")
    
    try:
        # 파일 크기 확인
        response = requests.head(model_url)
        file_size = int(response.headers.get('content-length', 0))
        
        if file_size == 0:
            print("❌ 파일 크기를 확인할 수 없습니다.")
            return False
        
        print(f"📦 파일 크기: {file_size / (1024**3):.2f} GB")
        print("🔄 다운로드 중... (시간이 오래 걸릴 수 있습니다)")
        
        # 다운로드
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        downloaded = 0
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % (10 * 1024 * 1024) == 0:  # 10MB마다 진행상황 출력
                        progress = (downloaded / file_size) * 100
                        print(f"📥 진행률: {progress:.1f}% ({downloaded / (1024**3):.2f} GB / {file_size / (1024**3):.2f} GB)")
        
        print(f"✅ 다운로드 완료: {model_path}")
        
        # 파일 크기 확인
        actual_size = os.path.getsize(model_path)
        if actual_size < 100 * 1024 * 1024:  # 100MB 미만이면 문제
            print(f"⚠️  파일 크기가 너무 작습니다: {actual_size / (1024**3):.2f} GB")
            os.remove(model_path)
            return False
        
        print(f"✅ 파일 크기 확인: {actual_size / (1024**3):.2f} GB")
        return True
        
    except Exception as e:
        print(f"❌ 다운로드 실패: {str(e)}")
        if os.path.exists(model_path):
            os.remove(model_path)
        return False

if __name__ == "__main__":
    print("Phi-3.5 3.8B GGUF 모델 다운로드")
    print("=" * 50)
    
    success = download_phi_3_5()
    
    if success:
        print("\n✅ 다운로드 성공!")
        print("이제 Phi-3.5 3.8B 모델을 사용할 수 있습니다.")
    else:
        print("\n❌ 다운로드 실패!")
        sys.exit(1) 
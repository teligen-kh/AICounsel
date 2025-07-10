# AI 상담사 파인튜닝 도구

Phi-3.5 3.8B 모델을 상담사 특화 모델로 파인튜닝하는 도구입니다.

## 📋 목차

- [개요](#개요)
- [시스템 요구사항](#시스템-요구사항)
- [설치](#설치)
- [사용법](#사용법)
- [클라우드 GPU 지원](#클라우드-gpu-지원)
- [문제 해결](#문제-해결)

## 🎯 개요

이 도구는 다음과 같은 기능을 제공합니다:

- **데이터 전처리**: FAQ CSV 데이터와 대화 데이터를 파인튜닝 형식으로 변환
- **LoRA 파인튜닝**: 메모리 효율적인 파인튜닝 (GTX 1050 Ti 지원)
- **GUI 인터페이스**: 사용자 친화적인 파인튜닝 설정 및 모니터링
- **모델 테스트**: 파인튜닝된 모델의 성능 평가
- **클라우드 지원**: 향후 AWS, GCP, Azure GPU 서버 지원 예정

## 💻 시스템 요구사항

### 최소 요구사항 (GTX 1050 Ti)
- **GPU**: NVIDIA GTX 1050 Ti (4GB VRAM)
- **RAM**: 8GB
- **저장공간**: 10GB
- **OS**: Windows 10/11, Linux, macOS

### 권장 사양
- **GPU**: RTX 3070 이상 (8GB+ VRAM)
- **RAM**: 16GB+
- **저장공간**: 20GB+

## 📦 설치

### 1. 저장소 클론
```bash
cd backend/finetune_tool
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. GPU 드라이버 확인
```bash
nvidia-smi
```

## 🚀 사용법

### 1. 파인튜닝 실행 (GPU 컴퓨터)

#### GUI 방식 (권장)
```bash
python run_finetune_gui.py
```

#### 명령행 방식
```bash
python -c "
from config import config_manager
from data_processor import DataProcessor
from model_trainer import ModelTrainer

# 데이터 처리
processor = DataProcessor(config_manager)
train_dataset, val_dataset, test_dataset = processor.process_all_data()

# 파인튜닝
trainer = ModelTrainer(config_manager)
trainer.train(train_dataset, val_dataset)
trainer.save_model()
"
```

### 2. 모델 테스트 (개발 컴퓨터)

#### 시나리오 테스트
```bash
python test_tool/run_model_test.py --model_path ./finetuned_models/finetuned_phi_20241201_143022 --test_type scenarios
```

#### 비교 테스트
```bash
python test_tool/run_model_test.py --model_path ./finetuned_models/finetuned_phi_20241201_143022 --test_type comparison --original_model microsoft/Phi-3.5-mini
```

#### 대화형 테스트
```bash
python test_tool/run_model_test.py --model_path ./finetuned_models/finetuned_phi_20241201_143022 --test_type interactive
```

## ☁️ 클라우드 GPU 지원

### 현재 지원
- **로컬 GPU**: GTX 1050 Ti 이상

### 향후 지원 예정
- **AWS**: g4dn.xlarge, p3.2xlarge
- **GCP**: n1-standard-4 + Tesla T4
- **Azure**: Standard_NC4as_T4_v3

### 클라우드 사용 시 워크플로우
1. 데이터를 클라우드 스토리지에 업로드
2. 클라우드 GPU 인스턴스에서 파인튜닝 실행
3. 파인튜닝된 모델을 로컬로 다운로드
4. 로컬에서 테스트 및 적용

## ⚙️ 설정

### 기본 설정 파일
```python
# config.py에서 수정 가능
finetune_config = {
    "model_name": "microsoft/Phi-3.5-mini",
    "lora_r": 16,
    "lora_alpha": 32,
    "num_epochs": 3,
    "learning_rate": 2e-4,
    "batch_size": 1,  # GTX 1050 Ti용
    "use_4bit": True  # 메모리 절약
}
```

### 하드웨어별 권장 설정

#### GTX 1050 Ti (4GB)
```python
{
    "batch_size": 1,
    "gradient_accumulation_steps": 16,
    "use_4bit": True,
    "max_seq_length": 512
}
```

#### RTX 3070 (8GB)
```python
{
    "batch_size": 2,
    "gradient_accumulation_steps": 8,
    "use_4bit": True,
    "max_seq_length": 1024
}
```

#### RTX 4090 (24GB)
```python
{
    "batch_size": 8,
    "gradient_accumulation_steps": 2,
    "use_4bit": False,
    "max_seq_length": 2048
}
```

## 📊 성능 예상

### GTX 1050 Ti 기준
- **데이터**: 300개 FAQ + 대화 데이터
- **예상 시간**: 2-4시간
- **메모리 사용량**: 4-6GB
- **모델 크기**: ~100MB (LoRA 어댑터)

### 성능 개선 예상
- **키워드 매칭률**: 60-80%
- **응답 품질**: 40-60% 개선
- **상담 전문성**: 50-70% 향상

## 🔧 문제 해결

### 일반적인 문제

#### 1. CUDA 메모리 부족
```
RuntimeError: CUDA out of memory
```
**해결책**:
- `batch_size`를 1로 설정
- `gradient_accumulation_steps`를 16으로 증가
- `use_4bit: True` 설정

#### 2. 패키지 설치 오류
```
ImportError: No module named 'transformers'
```
**해결책**:
```bash
pip install -r requirements.txt
```

#### 3. 모델 로드 실패
```
OSError: Can't load tokenizer
```
**해결책**:
- 인터넷 연결 확인
- Hugging Face 토큰 설정
- 모델 경로 확인

### 로그 확인
```bash
# 상세 로그 보기
python run_finetune_gui.py --verbose

# 로그 파일 확인
tail -f finetune.log
```

## 📁 파일 구조

```
finetune_tool/
├── config.py              # 설정 관리
├── data_processor.py      # 데이터 전처리
├── model_trainer.py       # 모델 훈련
├── requirements.txt       # 의존성
├── run_finetune_gui.py    # GUI 실행
├── gui/
│   └── main_window.py     # GUI 메인 윈도우
└── test_tool/
    ├── model_tester.py    # 모델 테스트
    └── run_model_test.py  # 테스트 실행
```

## 🤝 기여

버그 리포트나 기능 요청은 이슈로 등록해주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
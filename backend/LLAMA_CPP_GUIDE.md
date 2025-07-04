# llama-cpp-python 통합 가이드

## 📋 개요

이 가이드는 AI 상담 서비스에 llama-cpp-python을 통합하여 CPU 환경에서 효율적으로 LLM을 실행하는 방법을 설명합니다.

## 🎯 목표

- **성능 향상**: CPU에서 더 빠른 추론 속도
- **메모리 효율성**: 더 적은 메모리 사용량
- **확장성**: GPU 지원 준비
- **안정성**: 기존 아키텍처와의 호환성 유지

## 🚀 설치 및 설정

### 1. 자동 설치 스크립트 실행

```bash
cd backend
python install_llama_cpp.py
```

### 2. 수동 설치 (선택사항)

#### 패키지 설치
```bash
pip install llama-cpp-python
```

#### GGUF 모델 다운로드
```bash
# Polyglot-Ko 5.8B
wget -O models/polyglot-ko-5.8b-Q4_K_M.gguf \
  https://huggingface.co/TheBloke/polyglot-ko-5.8B-GGUF/resolve/main/polyglot-ko-5.8b.Q4_K_M.gguf

# LLaMA 3.1 8B Instruct
wget -O models/llama-3.1-8b-instruct-Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q4_K_M.gguf
```

### 3. 환경 변수 설정

```bash
# Windows
set USE_LLAMA_CPP=true

# Linux/Mac
export USE_LLAMA_CPP=true
```

또는 `.env` 파일 생성:
```env
USE_LLAMA_CPP=true
DEFAULT_MODEL_TYPE=polyglot-ko-5.8b
LLAMA_CPP_N_THREADS=8
LLAMA_CPP_N_CTX=2048
```

## 🔧 사용 방법

### 1. 서버 실행

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. API 테스트

```bash
# 기본 채팅 테스트
curl -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'

# 상세 응답 확인
curl -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "고객 상담에 대해 알려주세요"}' \
  -v
```

### 3. 모델 전환

```python
# 코드에서 모델 전환
llm_service = await get_llm_service()
llm_service.switch_model("polyglot-ko-5.8b")  # 또는 "llama-3.1-8b"
```

## 📊 성능 비교

### Transformers vs llama-cpp-python

| 항목 | Transformers | llama-cpp-python |
|------|-------------|------------------|
| 초기 로딩 | 30-60초 | 5-15초 |
| 응답 시간 | 15-25초 | 3-8초 |
| 메모리 사용량 | 8-12GB | 2-4GB |
| CPU 사용률 | 높음 | 중간 |
| GPU 지원 | 완전 | 제한적 |

### 최적화된 파라미터

#### Polyglot-Ko 5.8B
```python
{
    "max_tokens": 50,        # 짧은 응답으로 속도 향상
    "temperature": 0.5,      # 일관성 있는 응답
    "top_p": 0.7,           # 안정적인 생성
    "top_k": 40,            # 품질과 속도 균형
    "repeat_penalty": 1.1,  # 반복 방지
    "stop": ["\n\n", "사용자:", "질문:"]  # 자연스러운 중단
}
```

## 🛠️ 문제 해결

### 1. 모델 로딩 실패

**증상**: `FileNotFoundError: Model file not found`

**해결책**:
```bash
# 모델 파일 확인
ls -la models/*.gguf

# 모델 다운로드 재시도
python install_llama_cpp.py
```

### 2. 메모리 부족

**증상**: `OutOfMemoryError`

**해결책**:
```python
# llama_cpp_processor.py에서 파라미터 조정
self.llm = Llama(
    model_path=self.model_path,
    n_ctx=1024,        # 컨텍스트 길이 줄이기
    n_threads=4,       # 스레드 수 줄이기
    n_gpu_layers=0,    # GPU 사용 안함
    verbose=False
)
```

### 3. 응답 품질 저하

**증상**: 무의미한 응답 또는 노이즈

**해결책**:
```python
# 후처리 필터링 강화
meaningless_patterns = [
    r'※.*발생하고 있습니다',
    r'안녕하세용~',
    r'ㅎㅎ',
    # 추가 패턴...
]
```

### 4. 성능 최적화

**CPU 스레드 수 조정**:
```python
# 시스템에 맞게 조정
n_threads = min(8, os.cpu_count())  # CPU 코어 수에 맞춤
```

**컨텍스트 길이 최적화**:
```python
# 대화 길이에 맞게 조정
n_ctx = 2048  # 짧은 대화: 1024, 긴 대화: 4096
```

## 🔄 폴백 메커니즘

llama-cpp-python 초기화 실패 시 자동으로 Transformers로 폴백됩니다:

```python
try:
    self._initialize_llama_cpp()
except Exception as e:
    logging.warning("llama-cpp 초기화 실패, Transformers로 폴백")
    self.use_llama_cpp = False
    self._initialize_transformers()
```

## 📈 모니터링

### 성능 메트릭 확인

```python
# 응답 통계 확인
stats = llm_service.get_response_stats()
print(f"평균 처리 시간: {stats['total_processing_time'] / stats['total_requests']:.2f}ms")
print(f"성공률: {(stats['total_requests'] - stats['errors']) / stats['total_requests'] * 100:.1f}%")
```

### 로그 확인

```bash
# 실시간 로그 모니터링
tail -f backend/logs/app.log | grep "llama-cpp"
```

## 🚀 GPU 지원 (향후 계획)

### CUDA 지원 설치

```bash
# CUDA 지원 버전 설치
pip install llama-cpp-python[server] --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/
```

### GPU 설정

```python
self.llm = Llama(
    model_path=self.model_path,
    n_gpu_layers=35,  # GPU 레이어 수 (모델 크기에 따라 조정)
    n_threads=8,
    verbose=False
)
```

## 📝 체크리스트

- [ ] llama-cpp-python 설치 완료
- [ ] GGUF 모델 다운로드 완료
- [ ] 환경 변수 설정 완료
- [ ] 서버 실행 및 테스트 완료
- [ ] 성능 확인 완료
- [ ] 폴백 메커니즘 테스트 완료

## 🆘 지원

문제가 발생하면 다음을 확인하세요:

1. **로그 확인**: `backend/logs/app.log`
2. **모델 파일 확인**: `models/` 디렉토리
3. **환경 변수 확인**: `echo $USE_LLAMA_CPP`
4. **의존성 확인**: `pip list | grep llama-cpp`

추가 지원이 필요하면 프로젝트 이슈를 생성해주세요. 
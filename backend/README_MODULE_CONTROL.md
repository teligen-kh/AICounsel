# AICounsel 모듈 제어 가이드

## 📋 개요

AICounsel 프로젝트는 코드 한 두 줄로 모듈을 활성화/비활성화할 수 있는 유연한 구조로 설계되었습니다. 
이를 통해 다양한 테스트 시나리오와 운영 모드를 쉽게 전환할 수 있습니다.

**주요 특징:**
- 🎯 **간단한 제어**: 코드 한 두 줄로 모듈 전환
- 🔄 **동적 활성화**: 런타임에 모듈 상태 변경
- 📊 **상세한 통계**: 모듈별 성능 모니터링
- 🛠️ **유연한 구성**: 다양한 조합으로 시스템 구성

## 🔧 주요 모듈

### 1. LLM 모델과 MongoDB 연동 모듈
- **`mongodb_search`**: MongoDB에서 데이터를 검색하고 가져오는 모듈
- **`llm_model`**: LLM 모델과 연동하여 응답을 생성하는 모듈

### 2. 고객 질문 분석 및 응대 모듈
- **`conversation_analysis`**: 고객 질문을 분석하고 분류하는 알고리즘
- **`input_filtering`**: 입력 필터링 및 분류
- **`response_formatting`**: 응답 포맷팅
- **`db_priority`**: DB 우선 모드 (MongoDB 검색 우선)

## 🚀 사용 방법

### 기본 사용법

```python
from app.config import enable_module, disable_module, get_module_status

# 모듈 활성화
enable_module("mongodb_search")
enable_module("conversation_analysis")

# 모듈 비활성화
disable_module("input_filtering")

# 모듈 상태 확인
status = get_module_status()
print(status)
```

### 명령줄 사용법

```bash
# 모듈 상태 확인
python module_control.py status

# 모듈 활성화
python module_control.py enable mongodb_search

# 모듈 비활성화
python module_control.py disable input_filtering

# 모든 모듈 초기화
python module_control.py reset
```

### API 사용법

```bash
# 모듈 상태 조회
curl -X GET "http://localhost:8000/api/v1/modules/status"

# 모듈 활성화
curl -X POST "http://localhost:8000/api/v1/modules/control" \
  -H "Content-Type: application/json" \
  -d '{"module_name": "mongodb_search", "action": "enable"}'

# 모듈 비활성화
curl -X POST "http://localhost:8000/api/v1/modules/control" \
  -H "Content-Type: application/json" \
  -d '{"module_name": "input_filtering", "action": "disable"}'

# 모든 모듈 초기화
curl -X POST "http://localhost:8000/api/v1/modules/reset"
```

## 🎯 사용 시나리오

### 1. 순수 LLM 모드 (MongoDB 검색 비활성화)
```python
disable_module("mongodb_search")
disable_module("conversation_analysis")
```
- **용도**: LLM 모델만으로 응답 생성 테스트
- **특징**: MongoDB 검색 없이 순수 LLM 응답

### 2. DB 우선 모드
```python
enable_module("mongodb_search")
enable_module("db_priority")
```
- **용도**: MongoDB 데이터 우선 사용
- **특징**: DB에서 먼저 검색, 없으면 LLM 사용

### 3. 전체 분석 모드
```python
enable_module("mongodb_search")
enable_module("llm_model")
enable_module("conversation_analysis")
enable_module("response_formatting")
enable_module("input_filtering")
disable_module("db_priority")
```
- **용도**: 모든 기능 활성화
- **특징**: 고객 질문 분석 후 적절한 응답

### 4. 테스트 모드 (최소 기능)
```python
enable_module("llm_model")
disable_module("mongodb_search")
disable_module("conversation_analysis")
disable_module("response_formatting")
disable_module("input_filtering")
```
- **용도**: 기본 기능만 테스트
- **특징**: LLM 모델만 사용

## 📊 모듈 상태 확인

### Python에서 확인
```python
from app.config import print_module_status

print_module_status()
```

### 출력 예시
```
=== 모듈 활성화 상태 ===
mongodb_search: ✅ 활성화
llm_model: ✅ 활성화
conversation_analysis: ✅ 활성화
response_formatting: ✅ 활성화
input_filtering: ❌ 비활성화
db_priority_mode: ❌ 비활성화
=======================
```

## 🔄 동적 모듈 제어

모듈은 런타임에 동적으로 제어됩니다. 설정을 변경하면 다음 요청부터 새로운 설정이 적용됩니다.

```python
# 런타임에 모듈 전환
enable_module("mongodb_search")    # 즉시 MongoDB 검색 활성화
disable_module("input_filtering")  # 즉시 입력 필터링 비활성화
```

## 🛠️ 개발자 가이드

### 새로운 모듈 추가

1. `app/config.py`에 설정 추가:
```python
ENABLE_NEW_MODULE: bool = True
```

2. 제어 함수에 추가:
```python
def enable_module(module_name: str):
    if module_name == "new_module":
        settings.ENABLE_NEW_MODULE = True
    # ... 기존 코드

def disable_module(module_name: str):
    if module_name == "new_module":
        settings.ENABLE_NEW_MODULE = False
    # ... 기존 코드
```

3. 서비스에서 조건부 사용:
```python
if settings.ENABLE_NEW_MODULE:
    # 새 모듈 사용
    pass
else:
    # 기본 동작
    pass
```

### 모듈 의존성 관리

모듈 간 의존성이 있는 경우 주의해서 설정해야 합니다:

```python
# 예: MongoDB 검색이 비활성화되면 DB 우선 모드도 비활성화
if not settings.ENABLE_MONGODB_SEARCH:
    settings.DB_PRIORITY_MODE = False
```

## 📝 예제 실행

```bash
# 예제 스크립트 실행
cd backend
python module_examples.py
```

이 스크립트는 다양한 모듈 조합을 보여주는 예제를 실행합니다.

## 🔍 문제 해결

### 모듈이 활성화되지 않는 경우
1. 설정 파일 확인: `app/config.py`
2. 서비스 재시작
3. 로그 확인

### API 오류가 발생하는 경우
1. 서버 상태 확인
2. API 엔드포인트 확인
3. 요청 형식 확인

## 📞 지원

모듈 제어 기능에 대한 문의사항이 있으시면 개발팀에 연락해주세요. 
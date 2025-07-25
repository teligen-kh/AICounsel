# 구글 API 설정 - 워크플로우 ID 사용 (권장)

## 🔐 워크플로우 ID 인증 방법

### 1단계: 워크플로우 ID 생성
1. Google Cloud Console에서 "IAM 및 관리" → "워크플로우" 클릭
2. "워크플로우 만들기" 클릭
3. 워크플로우 이름: `aicounsel-sheets-workflow`
4. 지역: `asia-northeast3` (서울) 선택
5. "만들기" 클릭

### 2단계: 워크플로우 설정
1. 생성된 워크플로우 클릭
2. "편집" 클릭
3. 워크플로우에 Google Sheets API 접근 권한 추가

## 🚀 대안: Application Default Credentials (ADC)

### 1단계: gcloud CLI 설치
1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) 다운로드
2. 설치 후 터미널에서 인증:
```bash
gcloud auth application-default login
```

### 2단계: 스크립트 수정
```python
# google_credentials.json 대신 ADC 사용
import google.auth
credentials, project = google.auth.default()
```

## 📋 방법 2: CSV 파일 사용 (즉시 가능)

### 현재 상황에서 가장 빠른 해결책
```bash
cd D:\AICounsel\backend
python -m app.scripts.import_csv_safe
```

## 🔧 방법 3: 조직 관리자에게 요청

### 필요한 권한
- `roles/orgpolicy.policyAdmin` 역할
- 조직 정책 관리자 권한

### 요청 내용
```
정책 ID: iam.disableServiceAccountKeyCreation
상태: 사용 중지 요청
사유: AI Counsel 프로젝트용 서비스 계정 키 생성 필요
```

## 🎯 추천 순서

### 1순위: CSV 파일 사용 (즉시)
- 설정 없이 바로 사용 가능
- 쉼표 이슈 해결된 안전한 스크립트

### 2순위: gcloud ADC 사용
- 추가 설정 필요하지만 안전
- 서비스 계정 키 없이 인증

### 3순위: 조직 관리자 요청
- 시간이 오래 걸릴 수 있음
- 보안 정책 변경 필요

## 🚀 즉시 진행 가능한 방법

현재 상황에서는 **개선된 CSV 스크립트**를 사용하는 것이 가장 빠릅니다:

```bash
cd D:\AICounsel\backend
python -m app.scripts.import_csv_safe
```

이 방법으로 먼저 데이터를 가져오고, 나중에 구글 API 설정을 완료하시겠어요? 
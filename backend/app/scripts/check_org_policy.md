# 조직 정책 확인 및 해결 방법

## 🔍 1단계: 조직 구조 확인

### 1.1 현재 조직 확인
1. Google Cloud Console에서 **"IAM 및 관리"** → **"조직"** 클릭
2. 현재 조직 ID 확인
3. 상위 조직이 있는지 확인

### 1.2 정책 상속 경로 확인
1. **"조직 정책"** → **"정책"** 탭
2. `iam.disableServiceAccountKeyCreation` 정책 클릭
3. **"상속됨"** 섹션에서 상속 경로 확인
4. 어떤 조직에서 정책이 설정되었는지 확인

## 🔧 2단계: 상위 조직 관리자에게 요청

### 2.1 상위 조직 관리자 찾기
1. **"IAM 및 관리"** → **"IAM"** 클릭
2. `roles/orgpolicy.policyAdmin` 역할을 가진 사용자 찾기
3. 또는 `roles/resourcemanager.organizationAdmin` 역할을 가진 사용자 찾기

### 2.2 요청 내용
```
정책 ID: iam.disableServiceAccountKeyCreation
요청 사항: AI Counsel 프로젝트용 서비스 계정 키 생성 허용
사유: 개발 프로젝트에서 Google Sheets API 연동 필요
```

## 🚀 3단계: 대안 방법 사용

### 3.1 Application Default Credentials (ADC) 사용
```bash
# Google Cloud SDK 설치 후
gcloud auth application-default login
```

### 3.2 워크로드 ID 페더레이션 사용
- 서비스 계정 키 없이 인증
- 더 안전한 방법

### 3.3 CSV 파일 사용 (즉시 가능)
```bash
cd D:\AICounsel\backend
python -m app.scripts.import_csv_safe
```

## 📋 4단계: 조직 정책 우회 방법

### 4.1 개인 프로젝트 생성
1. 개인 구글 계정으로 새 프로젝트 생성
2. 조직 정책의 영향을 받지 않음
3. 서비스 계정 키 생성 가능

### 4.2 다른 조직 계정 사용
1. 다른 구글 계정으로 프로젝트 생성
2. 조직 정책이 없는 환경에서 작업

## 🎯 추천 해결 순서

### 1순위: CSV 파일 사용 (즉시)
- 설정 없이 바로 사용 가능
- 조직 정책과 무관

### 2순위: 상위 조직 관리자 요청
- 정책 변경 요청
- 시간이 걸릴 수 있음

### 3순위: 개인 프로젝트 사용
- 조직 정책 우회
- 추가 설정 필요

## 🚀 즉시 진행 가능한 방법

현재 상황에서는 **CSV 파일 사용**이 가장 빠릅니다:

```bash
cd D:\AICounsel\backend
python -m app.scripts.import_csv_safe
```

이 방법으로 먼저 데이터를 가져오고, 나중에 구글 API 설정을 완료하시겠어요? 
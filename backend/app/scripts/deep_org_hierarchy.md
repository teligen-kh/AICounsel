# 깊은 조직 계층 구조 확인 방법

## 🔍 1단계: 조직 계층 구조 완전 확인

### 1.1 현재 조직 정보
- 조직 ID: `teligen.co.kr`
- 소유자: `teligendrive@teligen.co.kr` (이경호)
- 권한: 최고관리자 (211개 권한)

### 1.2 상위 조직 확인
1. **"IAM 및 관리"** → **"조직"** 클릭
2. **"상위 조직"** 섹션 확인
3. 더 상위 조직이 있는지 확인

### 1.3 조직 계층 구조 탐색
```
가능한 구조:
상위 조직 (Parent)
├── teligen.co.kr (현재)
│   └── aicounsel-sheets (프로젝트)
└── 다른 하위 조직들
```

## 🏢 2단계: 조직 정책 상속 경로 추적

### 2.1 정책 상속 확인
1. **"조직 정책"** → **"정책"** 탭
2. `iam.disableServiceAccountKeyCreation` 정책 클릭
3. **"상속됨"** 섹션에서 상속 경로 확인

### 2.2 상속 경로 예시
```
상위 조직 정책 → teligen.co.kr → aicounsel-sheets
```

## 👥 3단계: 상위 조직 관리자 찾기

### 3.1 상위 조직 IAM 확인
1. 상위 조직 ID로 이동
2. **"IAM 및 관리"** → **"IAM"** 클릭
3. 다음 역할을 가진 사용자 찾기:
   - `roles/owner` (소유자)
   - `roles/resourcemanager.organizationAdmin` (조직 관리자)
   - `roles/orgpolicy.policyAdmin` (조직 정책 관리자)

### 3.2 조직 소유자 확인
- 상위 조직의 소유자가 누구인지 확인
- 해당 소유자에게 정책 해제 요청

## 🔧 4단계: 대안 방법들

### 4.1 즉시 사용 가능한 방법
```bash
cd D:\AICounsel\backend
python -m app.scripts.import_csv_safe
```

### 4.2 개인 프로젝트 생성
1. 개인 구글 계정으로 새 프로젝트 생성
2. 조직 정책의 영향을 받지 않음
3. 서비스 계정 키 생성 가능

### 4.3 Application Default Credentials (ADC)
```bash
# Google Cloud SDK 설치 후
gcloud auth application-default login
```

## 📋 5단계: 확인 체크리스트

### 현재 상황:
- [ ] 최고관리자 권한 보유 (211개 권한)
- [ ] teligen.co.kr 조직 소유자
- [ ] 정책 수정 비활성화
- [ ] 서비스 계정 키 생성 차단

### 확인 필요:
- [ ] 상위 조직 존재 여부
- [ ] 상위 조직 ID
- [ ] 상위 조직 소유자
- [ ] 정책 상속 경로

## 🚀 6단계: 추천 해결 순서

### 1순위: CSV 파일 사용 (즉시)
```bash
cd D:\AICounsel\backend
python -m app.scripts.import_csv_safe
```

### 2순위: 상위 조직 관리자 요청
- 상위 조직 소유자에게 정책 해제 요청
- 시간이 걸릴 수 있음

### 3순위: 개인 프로젝트 사용
- 조직 정책 우회
- 추가 설정 필요

## 🎯 결론

현재 상황에서는 **CSV 파일 사용**이 가장 빠르고 안전한 방법입니다.

상위 조직 구조를 확인하시고, 그동안 CSV로 데이터를 가져오시는 것을 추천합니다! 
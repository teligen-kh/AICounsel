# 구글 API 설정 - 1단계: 클라우드 콘솔 설정

## 🚀 1단계: 구글 클라우드 콘솔 접속

### 1.1 구글 클라우드 콘솔 열기
1. 브라우저에서 [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 구글 계정으로 로그인

### 1.2 새 프로젝트 생성
1. 상단의 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름 입력: `aicounsel-sheets`
4. "만들기" 클릭
5. 프로젝트가 생성될 때까지 대기 (약 1-2분)

### 1.3 프로젝트 선택
- 생성된 `aicounsel-sheets` 프로젝트 선택

## 🔧 2단계: API 활성화

### 2.1 Google Sheets API 활성화
1. 왼쪽 메뉴에서 "API 및 서비스" → "라이브러리" 클릭
2. 검색창에 "Google Sheets API" 입력
3. "Google Sheets API" 클릭
4. "사용" 버튼 클릭

### 2.2 Google Drive API 활성화
1. 다시 "라이브러리"로 이동
2. 검색창에 "Google Drive API" 입력
3. "Google Drive API" 클릭
4. "사용" 버튼 클릭

## 🔑 3단계: 서비스 계정 생성

### 3.1 사용자 인증 정보 생성
1. "API 및 서비스" → "사용자 인증 정보" 클릭
2. "사용자 인증 정보 만들기" 클릭
3. "서비스 계정" 선택

### 3.2 서비스 계정 설정
1. 서비스 계정 이름: `aicounsel-sheets-service`
2. 서비스 계정 ID: 자동 생성됨
3. 설명: `AI Counsel Google Sheets Integration`
4. "만들고 계속하기" 클릭

### 3.3 권한 설정
1. "역할 선택" → "편집자" 선택
2. "계속" 클릭
3. "완료" 클릭

### 3.4 키 생성
1. 생성된 서비스 계정 클릭
2. "키" 탭 클릭
3. "키 추가" → "새 키 만들기" 클릭
4. "JSON" 선택
5. "만들기" 클릭
6. JSON 파일이 자동으로 다운로드됨

## 📁 4단계: 파일 배치

### 4.1 JSON 파일 이름 변경
- 다운로드된 파일을 `google_credentials.json`으로 이름 변경

### 4.2 프로젝트에 배치
```
D:\AICounsel\backend\google_credentials.json
```

## ✅ 5단계: 확인

### 5.1 JSON 파일 내용 확인
- 파일을 열어서 `client_email` 값 확인
- 예: `aicounsel-sheets-service@aicounsel-sheets.iam.gserviceaccount.com`

### 5.2 다음 단계 준비
- 이 이메일 주소를 메모해두세요 (다음 단계에서 사용)

## 🎯 완료 조건
- ✅ 프로젝트 생성 완료
- ✅ Google Sheets API 활성화
- ✅ Google Drive API 활성화  
- ✅ 서비스 계정 생성
- ✅ JSON 키 파일 다운로드
- ✅ JSON 파일을 프로젝트에 배치

이 단계가 완료되면 다음 단계로 진행합니다! 
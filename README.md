# AI 상담 시스템

AI 기반의 상담 시스템으로, 사용자와의 대화를 분석하고 통계를 제공합니다.

## 시스템 요구사항

- Windows 10 이상
- Python 3.8 이상
- Node.js 20.x
- MongoDB 8.0
- Visual Studio Build Tools

## 설치 방법

### 1. 필수 프로그램 설치

`tools` 폴더의 설치 파일들을 사용하여 다음 프로그램들을 설치합니다:
- Node.js: `node-v20.9.0-x64.msi`
- MongoDB: `mongodb-windows-x86_64-8.0.10-signed.msi`
- Visual Studio Build Tools: `vs_BuildTools.exe`

### 2. 프로젝트 설정

#### 백엔드 설정
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### 프론트엔드 설정
```bash
cd frontend
npm install
```

#### MongoDB 설정
1. MongoDB 설치 후 데이터 디렉토리 생성:
```bash
mkdir mongodb\data
```

2. MongoDB 서비스 시작:
```bash
mongod --dbpath mongodb\data
```

#### LLM 모델 설정
1. `models` 폴더 생성:
```bash
mkdir models
```

2. LLM 모델 파일(`llama-2-7b-chat.Q4_K_M.gguf`)을 `models` 폴더에 복사

## 실행 방법

1. MongoDB 서버 시작:
```bash
mongod --dbpath mongodb\data
```

2. 백엔드 서버 시작:
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

3. 프론트엔드 서버 시작:
```bash
cd frontend
npm run dev
```

또는 `start_servers.bat` 파일을 실행하여 모든 서버를 한 번에 시작할 수 있습니다.

## 주요 기능

1. 실시간 채팅
   - 사용자와 AI 어시스턴트 간의 대화
   - 대화 기록 저장 및 조회

2. 대화 분석
   - 기본 통계 (총 대화 수, 메시지 수 등)
   - 대화 패턴 분석
   - 키워드 분석

## 프로젝트 구조

```
AICounsel/
├── backend/              # FastAPI 백엔드
│   ├── app/             # 애플리케이션 코드
│   ├── models/          # LLM 모델
│   └── requirements.txt # Python 의존성
├── frontend/            # Next.js 프론트엔드
│   ├── src/            # 소스 코드
│   └── package.json    # Node.js 의존성
├── mongodb/            # MongoDB 설정
└── tools/              # 설치 파일들
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
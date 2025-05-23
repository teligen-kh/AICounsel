# 고객 지원 플랫폼 PRD (Cursor 개발용)

## 프로젝트 개요
- **프로젝트명**: 특화 고객 지원 웹앱
- **목표**: 휴대폰으로 접근 가능한 웹앱을 만들어, Grok 또는 GPT가 MongoDB Atlas에 저장된 10,300개 FAQ와 상담 이력 데이터를 활용해 고객별 맞춤형 채팅/음성 지원 제공.
- **규모**: 연간 110,000~1,100,000콜 (하루 300~3,000콜), 상담사 4명 기준 10~100배 확장.
- **기간**: 3개월 (2025년 5월 23일 ~ 8월 23일)
- **예산**: 단독 7,569,000원~9,927,130원, 2인 팀 7,699,000원~10,217,130원
- **팀**: 단독 또는 2명 개발자, Cursor Pro로 코드 생성(85~95%) 및 디버깅(60~70%) 활용.

## 개발 도구
- **백엔드**: FastAPI (비동기 API, A2A 클라이언트, RAG)
- **프론트엔드**: Next.js (v15.0, App Router, SSR/SSG, Material-UI)
- **데이터베이스**: MongoDB Atlas (BSON/Atlas Search, M10 티어, 연 360,000원)
- **에이전트 서버**: Rocket.Chat (A2A 서버, Webhook, 무료)
- **AI API**: OpenAI Whisper (음성→텍스트), GPT-4o-mini (대화), TTS (텍스트→음성), 연 3,630,000원~5,658,130원
- **코딩 AI**: Cursor (Pro, 단독 3개월 60,000원~120,000원, 2인 120,000원~240,000원)
- **배포**: AWS Free Tier (EC2, 연 728,000원), Vercel (Next.js, 무료 티어)
- **기타**: GitHub (저장소), Docker (Rocket.Chat), Chart.js (보고서)

## 기능 요구사항
### 1. QR코드/웹앱 접근
- **설명**: 매장 직원/사장이 QR코드 또는 웹앱으로 음성/텍스트 상담 시작.
- **기능**:
  - QR코드 스캔으로 앱 접속.
  - 고객사별 브랜드 UI (로고, 색상).
- **A2A 활용** (무료 프로토콜):
  - Rocket.Chat A2A `auth/login`으로 OAuth 인증 (`skill: user_auth`).
  - Agent Card로 고객사별 인증 설정 광고 (예: `client_id: A`).
- **직접 개발**:
  - Next.js: SSR QR코드 페이지 (`qrcode.react`), 로그인 UI (Material-UI).
  - FastAPI: `/auth` 엔드포인트, Rocket.Chat Webhook 연동.
  - MongoDB: 사용자 인증 데이터 저장 (예: `db.users.find({"client_id": "A"})`).
- **커스터마이징**: 고객사별 UI 테마, 인증 방식 (OAuth/SSO).
- **소요 시간**: 1주 (Next.js 0.5주, FastAPI/MongoDB 0.5주).

### 2. 고객 확인 및 상담 이력 조회
- **설명**: AI가 고객 신원을 확인하고 이전 상담 이력 조회.
- **기능**:
  - ID/전화번호로 고객 검색.
  - 이전 상담 내역 표시 (예: 과거 문제, 해결).
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 고객 조회 (`skill: user_lookup`).
  - A2A `tasks/status`로 조회 진행 추적.
- **직접 개발**:
  - FastAPI: `/user` 엔드포인트, MongoDB 이력 조회.
  - MongoDB: 이력 검색 (예: `db.history.find({"client_id": "A"})`).
  - Next.js: 고객 정보 UI (CSR, Material-UI).
- **커스터마이징**: 고객사별 이력 필터 (예: A사 프린터 문제, B사 소프트웨어).
- **소요 시간**: 1주 (FastAPI/MongoDB 0.5주, Next.js 0.5주).

### 3. 용건 파악 (키워드 추출)
- **설명**: LLM이 정해진 순서로 고객 의도 파악.
- **기능**:
  - 음성/텍스트 입력에서 키워드 추출.
  - 분석용 의도 로그 저장.
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 의도 탐지 (`skill: intent_detection`).
  - 무료 A2A 샘플: 의도 분석 에이전트.
- **직접 개발**:
  - FastAPI: `/intent` 엔드포인트, GPT-4o-mini로 키워드 추출.
  - MongoDB: 의도 로그 (예: `db.intents.insertOne({"client_id": "A", "keyword": "printer_error"})`).
- **커스터마이징**: 고객사별 의도 규칙 (예: A사 하드웨어, B사 소프트웨어).
- **소요 시간**: 1주 (FastAPI/MongoDB 0.7주, Next.js 0.3주).

### 4. FAQ 검색 및 대화
- **설명**: AI가 키워드로 FAQ 검색, 대화 이어감.
- **기능**:
  - 실시간 FAQ 검색, LLM 주도 대화.
  - 고객사별 FAQ 우선순위.
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 FAQ 검색 (`skill: faq_search`).
  - Agent Card: 고객사별 FAQ 설정 (예: `printer_faq`, `software_faq`).
  - A2A 멀티 에이전트: Salesforce CRM 조회 (`skill: crm_lookup`).
- **직접 개발**:
  - FastAPI: `/chat` 엔드포인트, A2A+RAG, GPT-4o-mini 응답.
  - MongoDB: FAQ 검색 (Atlas Search, `db.faq.find({"client_id": "A", "question": {"$regex": "printer_error"}})`).
  - Next.js: 채팅 UI (Socket.IO, CSR).
- **커스터마이징**: 고객사별 FAQ (예: A사 프린터, B사 CRM), 워크플로우 우선순위.
- **소요 시간**: 1.5주 (FastAPI/MongoDB 1주, Next.js 0.5주).

### 5. 멀티모달 지원 (PDF/이미지)
- **설명**: PDF/이미지 송수신으로 이해 돕고, 고객 이미지 분석.
- **기능**:
  - 설명 PDF/이미지 전송.
  - 고객 이미지로 오류 해결.
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 미디어 전송 (`skill: media_transfer`).
  - A2A 상태: SSE로 전송/분석 추적.
- **직접 개발**:
  - FastAPI: `/media` 엔드포인트, OpenAI Vision API로 이미지 분석.
  - MongoDB: 미디어 메타데이터 (예: `db.media.insertOne({"client_id": "A", "type": "pdf"})`).
  - Next.js: PDF/이미지 표시 UI (CSR, Material-UI).
- **커스터마이징**: 고객사별 미디어 형식 (예: A사 매뉴얼 PDF, B사 스크린샷).
- **소요 시간**: 1.5주 (FastAPI/MongoDB 1주, Next.js 0.5주).

### 6. 외부 연동 (연구소/AS 파견)
- **설명**: 연구소 오류/출장 AS 요청 전달, 고객 알림.
- **기능**:
  - 연구소 오류 전달, 해결 피드백.
  - 출장 AS 일정 알림 (일자/시간).
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 파견 요청 (`skill: service_dispatch`).
  - A2A 멀티 에이전트: SAP로 AS 일정 관리.
  - A2A 상태: `tasks/status`로 진행/피드백.
- **직접 개발**:
  - FastAPI: `/service` 엔드포인트, 외부 API 호출.
  - MongoDB: 요청 로그 (예: `db.services.insertOne({"client_id": "A", "type": "as_schedule"})`).
  - Next.js: 알림 UI (CSR).
- **커스터마이징**: 고객사별 파견 규칙 (예: A사 연구소 우선, B사 AS 우선).
- **소요 시간**: 1주 (FastAPI/MongoDB 0.7주, Next.js 0.3주).

### 7. 데이터 저장 및 파인튜닝
- **설명**: 통화/이미지 텍스트 저장, LLM 파인튜닝으로 정확도 향상.
- **기능**:
  - 통화/이미지를 텍스트로 변환, DB 저장.
  - 새 데이터(300 → 10,300개)로 LLM 파인튜닝.
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 텍스트 변환/저장 (`skill: data_logging`).
  - 무료 A2A 샘플: 로깅 에이전트.
- **직접 개발**:
  - FastAPI: `/log` 엔드포인트, Whisper 텍스트 변환, OpenAI 파인튜닝 API.
  - MongoDB: 통화/이미지 텍스트 저장 (예: `db.history.insertOne({"client_id": "A", "text": "printer_error"})`).
  - 파인튜닝: OpenAI API (50,000원~200,000원, 300 → 10,300개).
- **커스터마이징**: 고객사별 파인튜닝 데이터 (예: A사 하드웨어 오류, B사 소프트웨어).
- **소요 시간**: 1.5주 (FastAPI/MongoDB 1주, 파인튜닝 0.5주).

### 8. 동시 접속 및 처리
- **설명**: 다중 동시 접속/요청 지원.
- **기능**:
  - 하루 300~3,000콜 동시 처리.
  - 실시간 DB 쿼리 최적화.
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 부하 분산 (`skill: load_balancing`).
  - A2A 상태: SSE로 동시 모니터링.
- **직접 개발**:
  - FastAPI: 비동기 처리 (uvicorn, 3,000콜/일).
  - MongoDB: 동시 쿼리 최적화 (Atlas Search 인덱스).
  - Next.js: 서버 컴포넌트로 동시 UI 렌더링.
- **커스터마이징**: 고객사별 부하 우선순위 (예: A사 음성, B사 채팅).
- **소요 시간**: 1주 (FastAPI/MongoDB 0.7주, Next.js 0.3주).

### 9. 보고서 시스템
- **설명**: 고객사 관리자가 웹으로 보고서 조회.
- **기능**:
  - 다중 조건 조회 (유형, 날짜, 만족도).
  - 시각적 차트 (예: 콜량, 만족도 추세).
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/send`로 보고서 쿼리 (`skill: report_query`).
  - A2A 상태: `tasks/status`로 쿼리 진행 추적.
- **직접 개발**:
  - FastAPI: `/report` 엔드포인트, MongoDB 집계.
  - MongoDB: 보고서 쿼리 (예: `db.history.aggregate([{"$match": {"client_id": "A"}}, {"$group": {"_id": "$type", "count": {"$sum": 1}}}]`)`).
  - Next.js: 보고서 UI (Chart.js, SSR).
- **커스터마이징**: 고객사별 지표 (예: A사 만족도, B사 콜 유형).
- **소요 시간**: 1주 (FastAPI/MongoDB 0.5주, Next.js 0.5주).

### 10. 배포 및 테스트
- **설명**: AWS/Vercel 배포, 한국어 음성/채팅 테스트, 보고서 검증.
- **기능**:
  - HTTPS, 확장 가능한 배포.
  - 100콜 테스트, 보고서 정확도 확인.
- **A2A 활용**:
  - Rocket.Chat A2A `tasks/status`로 테스트 응답 모니터링.
  - A2A 피드백: SSE로 고객사별 품질 피드백.
- **직접 개발**:
  - AWS EC2: FastAPI, Rocket.Chat Docker 배포.
  - Vercel: Next.js 배포 (무료 티어, HTTPS).
  - MongoDB Atlas: 10,300개 데이터 업로드.
  - 테스트: 100콜 한국어 음성/채팅, 보고서 검증.
- **커스터마이징**: 고객사별 테스트 시나리오 (예: A사 음성, B사 채팅).
- **소요 시간**: 2~2.5주 (배포 1주, 테스트 1~1.5주).

## 개발 일정
- **총 기간**: 단독 2.7~3개월 (주당 40~50시간), 2인 팀 2~2.5개월 (병렬 작업).
  - **1주**: PRD 검토, Cursor/Next.js 학습 (7일).
  - **2~3주**: 인증/QR코드, 고객 조회 (2주).
  - **4~5주**: 의도 파악, FAQ/대화 (2주).
  - **6~7주**: 멀티모달, 외부 연동 (2.5주).
  - **8~9주**: 데이터 저장/파인튜닝, 동시 처리 (2.5주).
  - **10주**: 보고서 (1주).
  - **11~12주**: 배포/테스트 (2~2.5주).
  - **마이그레이션**: MongoDB Atlas (3~5일, 구현 내 포함).

## 기술 스택
- **백엔드**: FastAPI, Python A2A 라이브러리, OpenAI API.
- **프론트엔드**: Next.js (v15.0, App Router), Material-UI, Socket.IO, WebRTC, Chart.js.
- **데이터베이스**: MongoDB Atlas (BSON/Atlas Search).
- **에이전트 서버**: Rocket.Chat (A2A, Webhook).
- **배포**: AWS EC2, Vercel, Docker, HTTPS.

## 리스크 및 완화
- **A2A 초기 버전 (2025년 4월)**: 문서/샘플 제한, 디버깅 부담.
  - **완화**: Cursor 디버깅(60~70%), Grok 가이드, A2A 커뮤니티.
- **Next.js 학습**: App Router로 1~2주 추가.
  - **완화**: Cursor 코드 생성, Grok 튜토리얼 (YouTube “Next.js 15 Crash Course”).
- **마이그레이션**: MySQL → MongoDB, 3~5일.
  - **완화**: Grok PyMongo 스크립트, Atlas Search 쿼리.
- **규모 (110만 콜)**: 성능 부담.
  - **완화**: MongoDB Atlas M30 (연 1,440,000원), Vercel 스케일링.

## 다음 단계
1. **PRD 검토** (1~2일): 고객사별 요구사항(예: FAQ 분류, CRM 연동) 확인, 팀 규모(단독/2명).
2. **개발 시작** (1주):
   - Cursor 설정 (VS Code import, `cursor` 명령어).
   - Next.js 프로젝트 (`npx create-next-app@15`).
   - Rocket.Chat `agent.json`으로 A2A 설정.
   - Grok 지원: Next.js/A2A 샘플 코드, MongoDB 쿼리.
3. **질문**:
   - 고객사 요구사항 상세, 데이터 샘플 제공.
   - 추가 Next.js/A2A 자료 요청.
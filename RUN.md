# 🚀 프로젝트 실행 가이드

## 전체 실행 순서

### 1️⃣ 백엔드 서버 실행

#### 방법 1: Polling 방식 (PAT 기반 구독 시스템) - 권장

```bash
# 프로젝트 루트 디렉토리에서
cd /Users/jiho/Desktop/projects/hackerton

# 가상환경 활성화
source venv/bin/activate

# 서버 실행
python main_with_polling.py
```

**실행 결과:**

```
🌙 NightWatch Server Starting...
Gemini API Key: ✓ Set
Slack Token: ✓ Set
Encryption Key: ✓ Set
✅ Database initialized
✅ Polling scheduler started (interval: 5 minutes)
🌐 Starting API server on port 5001...
 * Running on http://0.0.0.0:5001
```

#### 방법 2: Webhook 방식 (기존 방식)

```bash
# 가상환경 활성화
source venv/bin/activate

# 서버 실행
python main.py
```

**실행 결과:**

```
🌙 NightWatch Server Starting...
Gemini API Key: ✓ Set
Slack Token: ✓ Set
✅ Database initialized
 * Running on http://0.0.0.0:5000
```

### 2️⃣ 프론트엔드 실행 (별도 터미널)

```bash
# frontend 디렉토리로 이동
cd frontend

# 개발 서버 실행
npm run dev
```

**실행 결과:**

```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 3️⃣ 브라우저에서 접속

- **프론트엔드**: http://localhost:5173
- **백엔드 API**: http://localhost:5001 (Polling 방식) 또는 http://localhost:5000 (Webhook 방식)

## 📋 실행 전 체크리스트

### 필수 환경 변수 확인

`.env` 파일에 다음이 설정되어 있어야 합니다:

```bash
# 필수
GEMINI_API_KEY=your-key
SLACK_TOKEN=xoxb-your-token
SLACK_CHANNEL=#test-alerts
ENCRYPTION_KEY=your-encryption-key

# 선택사항
BASE_URL=global.oliveyoung.com
API_PORT=5001
POLLING_INTERVAL_MINUTES=5
```

### 패키지 설치 확인

```bash
# Python 패키지
pip install -r requirements.txt
playwright install chromium

# Node.js 패키지 (프론트엔드)
cd frontend
npm install
```

## 🔄 전체 실행 흐름

### 터미널 1: 백엔드 서버

```bash
cd /Users/jiho/Desktop/projects/hackerton
source venv/bin/activate
python main_with_polling.py
```

### 터미널 2: 프론트엔드

```bash
cd /Users/jiho/Desktop/projects/hackerton/frontend
npm run dev
```

### 브라우저

1. http://localhost:5173 접속
2. 레포지토리 구독 추가
3. PAT 입력 및 구독 설정
4. 자동으로 PR 감지 및 테스트 실행

## 🧪 테스트 방법

### 수동 테스트

```bash
# 가상환경 활성화
source venv/bin/activate

# 테스트 스크립트 실행
python test_manual.py
```

### API 테스트

```bash
# 헬스 체크
curl http://localhost:5001/health

# 구독 목록 조회
curl http://localhost:5001/api/subscriptions?user_id=user123
```

## 🐛 문제 해결

### 포트가 이미 사용 중

```bash
# 포트 확인
lsof -i :5001  # API 서버
lsof -i :5173  # 프론트엔드

# .env에서 포트 변경
API_PORT=5002
```

### 모듈을 찾을 수 없음

```bash
# 가상환경이 활성화되었는지 확인
which python  # venv/bin/python이어야 함

# 패키지 재설치
pip install -r requirements.txt
```

### 데이터베이스 오류

```bash
# 데이터베이스 재생성
rm nightwatch.db
python -c "from server.models import init_db; init_db()"
```

## 📝 실행 순서 요약

1. **환경 변수 설정** (`.env` 파일)
2. **백엔드 서버 실행** (`python main_with_polling.py`)
3. **프론트엔드 실행** (`cd frontend && npm run dev`)
4. **브라우저 접속** (http://localhost:5173)

## 🎯 다음 단계

서버가 실행되면:

1. 프론트엔드에서 레포지토리 구독 추가
2. PAT 입력 및 검증
3. 자동으로 PR 감지 및 테스트 실행
4. 결과 확인 (프론트엔드 또는 Slack)

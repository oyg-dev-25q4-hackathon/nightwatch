# 🚀 빠른 시작 가이드

## 프로젝트 실행 방법

### 1️⃣ 가상환경 활성화

```bash
# 프로젝트 디렉토리로 이동
cd /Users/jiho/Desktop/projects/hackerton

# 가상환경 활성화
source venv/bin/activate
```

가상환경이 활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다.

### 2️⃣ 패키지 설치 (처음 한 번만)

```bash
# 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 3️⃣ .env 파일 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 실제 값 입력:

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필수 항목만 설정해도 실행 가능)
# 최소 필수 항목:
# - GEMINI_API_KEY
# - SLACK_TOKEN
# - SLACK_CHANNEL
# - ENCRYPTION_KEY (PAT 방식 사용 시)
```

#### 암호화 키 생성 (PAT 방식 사용 시)

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

생성된 키를 `.env`의 `ENCRYPTION_KEY`에 설정하세요.

### 4️⃣ 서버 실행

#### 방법 1: Polling 방식 (PAT 기반 구독 시스템) - 권장

```bash
python main_with_polling.py
```

이 방식은:

- 레포지토리를 구독하면 자동으로 PR을 감지하고 테스트
- API 서버가 포트 5001에서 실행
- 5분마다 자동으로 PR 확인

#### 방법 2: Webhook 방식 (기존 방식)

```bash
python main.py
```

이 방식은:

- GitHub Webhook을 통해 PR 이벤트 수신
- 포트 5000에서 실행
- ngrok 등으로 외부 노출 필요

### 5️⃣ 서버 확인

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:

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

### 6️⃣ API 테스트

다른 터미널에서:

```bash
# 헬스 체크
curl http://localhost:5001/health

# 응답 예시:
# {"status": "healthy", "service": "nightwatch-api"}
```

## 📝 다음 단계

### Polling 방식 사용 시

1. **레포지토리 구독 추가**:

   ```bash
   curl -X POST http://localhost:5001/api/subscriptions \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "user123",
       "repo_full_name": "owner/repo-name",
       "pat": "ghp_your-github-pat-token",
       "auto_test": true,
       "slack_notify": true
     }'
   ```

2. **구독 목록 확인**:

   ```bash
   curl http://localhost:5001/api/subscriptions?user_id=user123
   ```

3. **자동 테스트**: 구독한 레포에 PR이 올라오면 자동으로 테스트 실행

### Webhook 방식 사용 시

1. **ngrok으로 외부 노출**:

   ```bash
   ngrok http 5000
   ```

2. **GitHub Webhook 설정**:
   - Repository → Settings → Webhooks → Add webhook
   - Payload URL: `https://your-ngrok-url.ngrok.io/webhook`
   - Content type: `application/json`
   - Secret: `.env`의 `GITHUB_WEBHOOK_SECRET` 값
   - Events: `Pull requests`

## 🔧 문제 해결

### 가상환경이 활성화되지 않음

```bash
# 가상환경이 없으면 생성
python3 -m venv venv
source venv/bin/activate
```

### 패키지 설치 오류

```bash
# pip 업그레이드
pip install --upgrade pip

# 패키지 재설치
pip install -r requirements.txt
```

### 포트가 이미 사용 중

```bash
# 포트 사용 확인
lsof -i :5001

# .env에서 다른 포트로 변경
API_PORT=5002
```

### 데이터베이스 오류

```bash
# 데이터베이스 재생성
rm nightwatch.db
python3 -c "from src.models import init_db; init_db()"
```

## 📚 더 자세한 정보

- **환경 설정**: [SETUP.md](SETUP.md) 참고
- **API 사용법**: [README_PAT.md](README_PAT.md) 참고
- **프로젝트 개요**: [README.md](README.md) 참고

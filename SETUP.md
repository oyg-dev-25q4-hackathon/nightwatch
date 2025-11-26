# 나이트워치 프로젝트 - 환경 설정 가이드

## 📋 사전 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)
- Git

## 🚀 단계별 설치 가이드

### 1단계: 프로젝트 클론 및 이동

```bash
# 프로젝트 디렉토리로 이동
cd /Users/jiho/Desktop/projects/hackerton
```

### 2단계: Python 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

가상환경이 활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다.

### 3단계: 패키지 설치

```bash
# 필요한 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (필수)
playwright install chromium
```

### 4단계: 암호화 키 생성

PAT를 암호화하기 위한 키를 생성해야 합니다.

#### 방법 1: Python으로 생성 (권장)

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

출력된 키를 복사해두세요. 예: `xK8jP2mN5qR7sT9vW1yZ3aB4cD6eF8gH0=`

#### 방법 2: Python 스크립트로 생성

```bash
python3 << EOF
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print("ENCRYPTION_KEY=" + key.decode())
EOF
```

### 5단계: .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# .env 파일 생성
touch .env
```

`.env` 파일 내용:

```bash
# ============================================
# Gemini API 설정
# ============================================
# Google AI Studio에서 API 키 발급: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# ============================================
# Slack 설정
# ============================================
# Slack App 생성 후 Bot Token 발급: https://api.slack.com/apps
SLACK_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=#test-alerts

# ============================================
# GitHub 설정 (선택사항)
# ============================================
# Webhook 방식 사용 시 필요 (Polling 방식에서는 선택사항)
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_WEBHOOK_SECRET=your-webhook-secret-here

# ============================================
# 웹사이트 설정
# ============================================
# 기본 웹사이트 URL (변경 가능)
BASE_URL=global.oliveyoung.com

# ============================================
# 쿠버네티스 설정
# ============================================
# 쿠버네티스 네임스페이스
K8S_NAMESPACE=default
# 배포 이름 접두사
DEPLOYMENT_PREFIX=pr-preview

# ============================================
# Browser MCP 설정
# ============================================
# Browser MCP 사용 여부 (true/false)
USE_BROWSER_MCP=true
# MCP 서버 URL (선택사항, 기본값: http://localhost:3000)
MCP_SERVER_URL=http://localhost:3000

# ============================================
# PAT 기반 구독 시스템 설정
# ============================================
# PAT 암호화 키 (4단계에서 생성한 키)
ENCRYPTION_KEY=xK8jP2mN5qR7sT9vW1yZ3aB4cD6eF8gH0=
# API 서버 포트
API_PORT=5001
# Polling 간격 (분)
POLLING_INTERVAL_MINUTES=5

# ============================================
# 데이터베이스 설정
# ============================================
# SQLite 데이터베이스 경로 (기본값: sqlite:///nightwatch.db)
DATABASE_URL=sqlite:///nightwatch.db
```

### 6단계: API 키 발급 방법

#### Gemini API 키 발급

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 생성된 API 키를 복사하여 `.env`의 `GEMINI_API_KEY`에 설정

#### Slack Bot Token 발급

1. [Slack API](https://api.slack.com/apps) 접속
2. "Create New App" 클릭
3. "From scratch" 선택
4. App 이름과 워크스페이스 선택
5. "OAuth & Permissions" 메뉴로 이동
6. "Bot Token Scopes"에 다음 권한 추가:
   - `chat:write` - 메시지 전송
   - `files:write` - 파일 업로드
7. "Install to Workspace" 클릭
8. 생성된 "Bot User OAuth Token" (xoxb-로 시작)을 `.env`의 `SLACK_TOKEN`에 설정
9. 알림을 받을 채널 이름을 `SLACK_CHANNEL`에 설정 (예: `#test-alerts`)

#### GitHub Personal Access Token 발급 (Polling 방식 사용 시)

1. GitHub에 로그인
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. "Generate new token (classic)" 클릭
4. Note: "NightWatch E2E Test" 입력
5. Expiration: 원하는 만료 기간 선택 (90일 권장)
6. Select scopes: `repo` (전체) 체크
   - 또는 Fine-grained token 사용 시:
     - Repository access: 특정 레포 선택
     - Permissions: Contents (Read), Pull requests (Read), Metadata (Read)
7. "Generate token" 클릭
8. 생성된 토큰을 복사 (한 번만 표시됨!)
9. 이 토큰은 API를 통해 입력하거나, `.env`의 `GITHUB_TOKEN`에 설정 (선택사항)

### 7단계: 디렉토리 구조 확인

필요한 디렉토리가 자동으로 생성되지만, 수동으로 생성하려면:

```bash
mkdir -p videos screenshots reports
```

### 8단계: 데이터베이스 초기화

서버 실행 시 자동으로 초기화되지만, 수동으로 초기화하려면:

```bash
python3 << EOF
from src.models import init_db
init_db()
print("✅ Database initialized")
EOF
```

### 9단계: 서버 실행

#### Polling 방식 (PAT 기반 구독 시스템)

```bash
python main_with_polling.py
```

#### Webhook 방식 (기존 방식)

```bash
python main.py
```

### 10단계: 서버 확인

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:

```
🌙 NightWatch Server Starting...
Gemini API Key: ✓ Set
Slack Token: ✓ Set
Encryption Key: ✓ Set (or ✗ Missing (will generate))
✅ Database initialized
✅ Polling scheduler started (interval: 5 minutes)
🌐 Starting API server on port 5001...
 * Running on http://0.0.0.0:5001
```

## 🧪 테스트

### API 서버 헬스 체크

```bash
curl http://localhost:5001/health
```

응답:
```json
{"status": "healthy", "service": "nightwatch-api"}
```

### PAT 검증 테스트

```bash
curl -X POST http://localhost:5001/api/pat/verify \
  -H "Content-Type: application/json" \
  -d '{"pat": "ghp_your-token-here"}'
```

## 🔧 문제 해결

### 문제 1: `ModuleNotFoundError`

**원인**: 가상환경이 활성화되지 않았거나 패키지가 설치되지 않음

**해결**:
```bash
# 가상환경 활성화 확인
which python  # venv/bin/python이어야 함

# 패키지 재설치
pip install -r requirements.txt
```

### 문제 2: `playwright` 명령어를 찾을 수 없음

**원인**: Playwright 브라우저가 설치되지 않음

**해결**:
```bash
playwright install chromium
```

### 문제 3: 암호화 키 오류

**원인**: ENCRYPTION_KEY가 설정되지 않았거나 잘못된 형식

**해결**:
```bash
# 새 키 생성
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# .env 파일에 추가
echo "ENCRYPTION_KEY=생성된_키" >> .env
```

### 문제 4: 데이터베이스 오류

**원인**: 데이터베이스 파일 권한 문제

**해결**:
```bash
# 데이터베이스 파일 삭제 후 재생성
rm nightwatch.db
python3 -c "from src.models import init_db; init_db()"
```

### 문제 5: 포트가 이미 사용 중

**원인**: 다른 프로세스가 포트를 사용 중

**해결**:
```bash
# 포트 사용 확인
lsof -i :5001  # macOS/Linux
netstat -ano | findstr :5001  # Windows

# .env에서 다른 포트로 변경
API_PORT=5002
```

## 📝 환경 변수 체크리스트

설정 완료 후 다음 항목을 확인하세요:

- [ ] `GEMINI_API_KEY` - Gemini API 키 설정
- [ ] `SLACK_TOKEN` - Slack Bot Token 설정
- [ ] `SLACK_CHANNEL` - Slack 채널 이름 설정
- [ ] `ENCRYPTION_KEY` - 암호화 키 설정 (PAT 사용 시 필수)
- [ ] `BASE_URL` - 기본 웹사이트 URL 설정
- [ ] `API_PORT` - API 서버 포트 설정 (기본값: 5001)
- [ ] `POLLING_INTERVAL_MINUTES` - Polling 간격 설정 (기본값: 5분)

## 🎯 다음 단계

환경 설정이 완료되면:

1. **레포지토리 구독**: API를 통해 레포지토리 구독 추가
2. **자동 테스트**: Polling이 자동으로 PR을 감지하고 테스트 실행
3. **결과 확인**: API 또는 Slack을 통해 테스트 결과 확인

자세한 API 사용법은 `README_PAT.md`를 참고하세요.


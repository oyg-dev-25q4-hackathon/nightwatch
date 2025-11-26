# 나이트워치 프로젝트 - Gemini API 버전

프로젝트 정리: 나이트워치 (NightWatch)

## 🎯 프로젝트 개요

"Sale is Coming..." - PR 기반 AI 자동 E2E 테스트 시스템

GitHub PR이 올라오면 자동으로 변경사항을 분석하고, 테스트 시나리오를 생성하여 실제 브라우저에서 검증한 뒤, 결과를 슬랙으로 전송하는 자동화 시스템입니다.

## 💡 핵심 가치 제안

- 개발자 시간 절약: 수동 E2E 테스트 불필요
- 배포 전 자동 검증: PR 단계에서 미리 문제 발견
- 시각적 증거 제공: 스크린샷/비디오로 버그 재현 용이

## 🏗️ 시스템 아키텍처

```
GitHub PR → Webhook → K8s 배포 (pr-123.global.oliveyoung.com)
                        ↓
                 LLM 분석 → 테스트 시나리오 생성
                        ↓
                 Browser MCP 실행
                        ↓
                 Vision API 검증
                        ↓
                 Slack 알림 + 리포트
```

자세한 다이어그램은 [docs/diagrams.md](docs/diagrams.md)를 참고하세요.

## 📁 프로젝트 구조 (MVC 패턴)

```
hackerton/
├── server/                     # 백엔드 서버 (MVC 구조)
│   ├── models/                # 데이터베이스 모델
│   │   ├── database.py
│   │   ├── user_credential.py
│   │   ├── subscription.py
│   │   └── test.py
│   ├── services/              # 비즈니스 로직
│   │   ├── pat_auth_service.py
│   │   ├── subscription_service.py
│   │   ├── polling_service.py
│   │   ├── test_pipeline_service.py
│   │   └── ...
│   ├── controllers/           # 컨트롤러
│   │   ├── subscription_controller.py
│   │   ├── pat_controller.py
│   │   └── test_controller.py
│   ├── routes/                # 라우팅
│   │   ├── api_routes.py
│   │   └── webhook_routes.py
│   ├── utils/                 # 유틸리티
│   │   └── crypto.py
│   ├── config/                # 설정
│   └── app.py                 # Flask 앱
│
├── frontend/                  # React 프론트엔드
│   └── src/
│       └── App.jsx
│
├── output/                    # 테스트 결과 파일
│   ├── videos/              # 테스트 영상
│   ├── screenshots/          # 스크린샷
│   └── reports/              # 테스트 리포트
├── main.py                    # Webhook 방식 서버
├── main_with_polling.py       # Polling 방식 서버
└── requirements.txt
```

자세한 구조는 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)를 참고하세요.

## 🔑 주요 기능

1. **쿠버네티스 자동 배포**: PR 생성 시 자동으로 `pr-{번호}.global.oliveyoung.com` 형태로 배포
2. **AI 기반 시나리오 생성**: Gemini API로 PR 변경사항 분석 후 테스트 시나리오 자동 생성
3. **Browser MCP 자동화**: Browser MCP를 사용하여 실제 브라우저에서 테스트 실행
4. **Vision 검증**: Gemini Vision API로 스크린샷 검증
5. **자동 정리**: PR이 닫히거나 머지될 때 배포 자동 정리

## 🔑 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# API Keys
GEMINI_API_KEY=your-gemini-api-key-here
SLACK_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#test-alerts
GITHUB_TOKEN=ghp_your-github-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# 웹사이트 설정
BASE_URL=global.oliveyoung.com  # 기본 웹사이트 URL (변경 가능)

# 쿠버네티스 설정
K8S_NAMESPACE=default  # 쿠버네티스 네임스페이스
DEPLOYMENT_PREFIX=pr-preview  # 배포 이름 접두사

# Browser MCP 설정
USE_BROWSER_MCP=true  # Browser MCP 사용 여부 (true/false)
MCP_SERVER_URL=http://localhost:3000  # MCP 서버 URL (선택사항)
```

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 서버 실행

```bash
python main.py
```

### 3. ngrok으로 외부 노출 (로컬 테스트용)

```bash
ngrok http 5000
```

나온 URL을 GitHub Webhook에 등록:

- Payload URL: `https://your-ngrok-url.ngrok.io/webhook`
- Content type: `application/json`
- Secret: `.env`의 `GITHUB_WEBHOOK_SECRET` 값
- Events: `Pull requests`

## 🧪 테스트 방법

### 수동 테스트

```bash
python test_manual.py
```

## 📦 주요 의존성

- `google-generativeai==0.3.2` - Gemini API
- `playwright==1.40.0` - 브라우저 자동화 (Browser MCP 폴백용)
- `flask==3.0.0` - Webhook 서버
- `slack-sdk==3.23.0` - Slack 알림
- `PyGithub==2.1.1` - GitHub API
- `requests==2.31.0` - HTTP 클라이언트 (MCP 통신용)

## 🔧 쿠버네티스 배포 설정

`src/k8s_deployer.py`의 `_execute_deployment` 메서드를 실제 환경에 맞게 수정해야 합니다:

- **kubectl 직접 사용**: `kubectl create deployment` 명령 사용
- **Helm 사용**: Helm chart를 사용한 배포
- **ArgoCD 사용**: ArgoCD를 통한 GitOps 배포

현재는 모의(Mock) 배포로 구현되어 있으며, 실제 쿠버네티스 환경에 맞게 수정이 필요합니다.

## 🌐 Browser MCP 설정

Browser MCP를 사용하려면 MCP 서버가 실행 중이어야 합니다. MCP 서버가 없을 경우 자동으로 Playwright로 폴백됩니다.

MCP 서버 URL은 환경 변수 `MCP_SERVER_URL`로 설정할 수 있으며, 기본값은 `http://localhost:3000`입니다.

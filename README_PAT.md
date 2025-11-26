# PAT 기반 레포지토리 구독 시스템 사용 가이드

## 🚀 빠른 시작

### 1. 환경 변수 설정

`.env` 파일에 다음을 추가:

```bash
# 기존 설정
GEMINI_API_KEY=your-gemini-api-key
SLACK_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#test-alerts
GITHUB_TOKEN=ghp_your-github-token  # (선택사항, Polling용)
BASE_URL=global.oliveyoung.com

# 새로운 설정
ENCRYPTION_KEY=your-encryption-key-here  # PAT 암호화용 (생성 방법 아래 참고)
API_PORT=5001  # API 서버 포트
POLLING_INTERVAL_MINUTES=5  # Polling 간격 (분)
```

### 2. 암호화 키 생성

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # 이 값을 ENCRYPTION_KEY에 설정
```

또는 자동 생성 (개발 환경):
- ENCRYPTION_KEY를 설정하지 않으면 자동으로 생성되지만, 재시작 시 복호화 불가
- 프로덕션에서는 반드시 환경 변수로 설정

### 3. 데이터베이스 초기화

서버 실행 시 자동으로 초기화됩니다.

### 4. 서버 실행

```bash
# Polling 기능 포함 서버 실행
python main_with_polling.py
```

## 📡 API 사용법

### 레포지토리 구독 추가

```bash
curl -X POST http://localhost:5001/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "repo_full_name": "company/repo-name",
    "pat": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "auto_test": true,
    "slack_notify": true,
    "target_branches": ["feature/*", "develop"],
    "test_options": {
      "scenario_count": 5,
      "namespace": "default"
    }
  }'
```

### 구독 목록 조회

```bash
curl http://localhost:5001/api/subscriptions?user_id=user123
```

### 구독 삭제

```bash
curl -X DELETE http://localhost:5001/api/subscriptions/1?user_id=user123
```

### PAT 검증

```bash
curl -X POST http://localhost:5001/api/pat/verify \
  -H "Content-Type: application/json" \
  -d '{
    "pat": "ghp_xxxxxxxxxxxxxxxxxxxx"
  }'
```

### 레포지토리 접근 확인

```bash
curl -X POST http://localhost:5001/api/pat/check-repo \
  -H "Content-Type: application/json" \
  -d '{
    "pat": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "repo_full_name": "company/repo-name"
  }'
```

### 테스트 기록 조회

```bash
curl http://localhost:5001/api/tests?user_id=user123&limit=10
```

## 🔄 동작 방식

1. **구독 추가**: 사용자가 레포지토리와 PAT를 입력
2. **PAT 검증**: GitHub API로 토큰 유효성 및 레포 접근 권한 확인
3. **암호화 저장**: PAT는 암호화되어 데이터베이스에 저장
4. **Polling 시작**: 5분마다 구독한 레포지토리의 PR 확인
5. **자동 테스트**: 새 PR 또는 업데이트된 PR 발견 시 자동 테스트 실행
6. **결과 저장**: 테스트 결과는 데이터베이스에 저장되고 Slack으로 알림

## 📊 데이터베이스 구조

- `user_credentials`: 암호화된 PAT 저장
- `subscriptions`: 구독 정보
- `tests`: 테스트 기록

## 🔒 보안 주의사항

1. **ENCRYPTION_KEY**: 반드시 안전하게 보관
2. **PAT**: GitHub에서 최소 권한으로 생성
3. **데이터베이스**: SQLite 파일 접근 제한
4. **HTTPS**: 프로덕션에서는 HTTPS 사용 필수

## 🐛 문제 해결

### PAT 검증 실패
- 토큰이 만료되었는지 확인
- 필요한 권한(repo)이 있는지 확인

### 레포지토리 접근 불가
- PAT에 해당 레포 접근 권한이 있는지 확인
- Private 레포인 경우 PAT에 repo 권한 필요

### Polling이 작동하지 않음
- 서버 로그 확인
- 데이터베이스에 구독 정보가 있는지 확인
- `auto_test`가 `true`인지 확인


# PAT 및 암호화 키 설정 가이드

## 🔑 두 가지 키의 차이

### 1. ENCRYPTION_KEY (암호화 키)

- **용도**: PAT를 암호화하기 위한 키
- **위치**: `.env` 파일에 저장
- **특징**: 한 번 생성하면 계속 사용 (변경하면 기존 암호화된 PAT 복호화 불가)

### 2. PAT (Personal Access Token)

- **용도**: GitHub 레포지토리에 접근하기 위한 토큰
- **위치**: API를 통해 입력하거나 임시로 `.env`에 저장 가능
- **특징**: GitHub에서 발급받은 실제 토큰

## 📝 설정 방법

### Step 1: ENCRYPTION_KEY 생성 및 설정

#### 방법 1: 명령어로 생성

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

출력 예시:

```
xK8jP2mN5qR7sT9vW1yZ3aB4cD6eF8gH0=
```

#### 방법 2: .env 파일에 직접 추가

생성된 키를 `.env` 파일에 추가:

```bash
# .env 파일 편집
nano .env
# 또는
vim .env
# 또는
code .env  # VS Code 사용 시
```

`.env` 파일에 다음 줄 추가:

```bash
ENCRYPTION_KEY=xK8jP2mN5qR7sT9vW1yZ3aB4cD6eF8gH0=
```

**⚠️ 중요**:

- 이 키는 **한 번만 생성**하고 계속 사용해야 합니다
- 키를 변경하면 기존에 암호화된 PAT를 복호화할 수 없습니다
- 키는 안전하게 보관하세요

### Step 2: 기존 PAT 활용

#### 방법 1: API를 통해 입력 (권장)

기존에 사용하던 PAT를 API를 통해 입력:

```bash
# 1. PAT 검증
curl -X POST http://localhost:5001/api/pat/verify \
  -H "Content-Type: application/json" \
  -d '{
    "pat": "ghp_기존에_사용하던_PAT_토큰"
  }'

# 2. 레포지토리 구독 추가 (PAT 포함)
curl -X POST http://localhost:5001/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "repo_full_name": "company/repo-name",
    "pat": "ghp_기존에_사용하던_PAT_토큰",
    "auto_test": true,
    "slack_notify": true
  }'
```

이렇게 하면:

- PAT가 암호화되어 데이터베이스에 저장됩니다
- `.env` 파일에 PAT를 저장할 필요가 없습니다 (더 안전)

#### 방법 2: .env에 임시로 저장 (개발용)

개발/테스트 목적으로만 `.env`에 임시 저장:

```bash
# .env 파일에 추가 (임시, 개발용만)
GITHUB_PAT=ghp_기존에_사용하던_PAT_토큰
```

**⚠️ 주의**:

- `.env` 파일은 Git에 커밋하지 마세요 (이미 .gitignore에 포함됨)
- 프로덕션에서는 API를 통해 입력하는 방식을 사용하세요

## 🔄 전체 설정 흐름

### 1. ENCRYPTION_KEY 설정 (한 번만)

```bash
# 1. 키 생성
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. .env 파일에 추가
echo "ENCRYPTION_KEY=생성된_키" >> .env
```

### 2. 서버 실행

```bash
source venv/bin/activate
python main_with_polling.py
```

### 3. 기존 PAT로 레포지토리 구독

```bash
# API를 통해 기존 PAT 입력
curl -X POST http://localhost:5001/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "repo_full_name": "company/private-repo",
    "pat": "ghp_기존에_사용하던_PAT",
    "auto_test": true
  }'
```

## ✅ 확인 방법

### ENCRYPTION_KEY가 제대로 설정되었는지 확인

```bash
# 서버 실행 시 확인
python main_with_polling.py

# 출력 예시:
# Encryption Key: ✓ Set  (정상)
# Encryption Key: ✗ Missing (will generate)  (키 없음, 자동 생성됨)
```

### PAT가 제대로 저장되었는지 확인

```bash
# 구독 목록 조회
curl http://localhost:5001/api/subscriptions?user_id=user123

# 응답에 구독 정보가 있으면 정상
```

## 🔒 보안 권장사항

1. **ENCRYPTION_KEY**:

   - 한 번 생성 후 계속 사용
   - `.env` 파일에만 저장 (Git에 커밋하지 않음)
   - 프로덕션에서는 환경 변수로 관리

2. **PAT**:
   - API를 통해 입력 (데이터베이스에 암호화되어 저장)
   - `.env` 파일에 저장하지 않음 (가능하면)
   - GitHub에서 최소 권한으로 생성

## 🐛 문제 해결

### 문제: "Failed to decrypt PAT"

**원인**: ENCRYPTION_KEY가 변경되었거나 없음

**해결**:

1. 기존 ENCRYPTION_KEY 확인
2. `.env` 파일에 올바른 키 설정
3. 키가 없으면 새로 생성하고 PAT를 다시 입력

### 문제: "Invalid or expired token"

**원인**: PAT가 만료되었거나 잘못된 토큰

**해결**:

1. GitHub에서 새 PAT 생성
2. API를 통해 새 PAT 입력

## 📋 요약

1. **ENCRYPTION_KEY**: `.env` 파일에 한 번만 설정 (PAT 암호화용)
2. **PAT**: API를 통해 입력하거나 `.env`에 임시 저장 (GitHub 접근용)
3. **기존 PAT 활용**: API의 `pat` 필드에 기존 PAT 입력하면 됨

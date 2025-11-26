# 프로젝트 구조 (MVC 패턴)

## 📁 디렉토리 구조

```
hackerton/
├── server/                    # 백엔드 서버 코드
│   ├── __init__.py
│   ├── app.py                # Flask 애플리케이션 메인
│   │
│   ├── models/               # 데이터베이스 모델 (M)
│   │   ├── __init__.py
│   │   ├── base.py           # SQLAlchemy Base
│   │   ├── database.py       # DB 설정 및 세션 관리
│   │   ├── user_credential.py
│   │   ├── subscription.py
│   │   └── test.py
│   │
│   ├── services/             # 비즈니스 로직 (Service Layer)
│   │   ├── __init__.py
│   │   ├── pat_auth_service.py
│   │   ├── subscription_service.py
│   │   ├── polling_service.py
│   │   ├── polling_scheduler.py
│   │   ├── test_pipeline_service.py
│   │   ├── pr_analyzer_service.py
│   │   ├── browser_executor.py
│   │   ├── browser_mcp_client.py
│   │   ├── vision_validator.py
│   │   ├── slack_notifier.py
│   │   └── k8s_deployer.py
│   │
│   ├── controllers/          # 컨트롤러 (C)
│   │   ├── __init__.py
│   │   ├── subscription_controller.py
│   │   ├── pat_controller.py
│   │   └── test_controller.py
│   │
│   ├── routes/               # 라우팅
│   │   ├── __init__.py
│   │   ├── api_routes.py     # API 라우트
│   │   └── webhook_routes.py # Webhook 라우트
│   │
│   ├── utils/                # 유틸리티
│   │   ├── __init__.py
│   │   └── crypto.py         # 암호화 유틸리티
│   │
│   └── config/               # 설정
│       └── __init__.py       # 환경 변수 설정
│
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── App.jsx
│   │   └── ...
│   └── ...
│
├── output/                   # 테스트 결과 파일
│   ├── videos/              # 테스트 영상
│   ├── screenshots/          # 스크린샷
│   └── reports/              # 테스트 리포트
│
├── main.py                   # Webhook 방식 서버
├── main_with_polling.py      # Polling 방식 서버
├── requirements.txt
├── .env
└── README.md
```

## 🏗️ 아키텍처 설명

### MVC 패턴 적용

#### Models (데이터베이스 모델)
- `server/models/`: SQLAlchemy 모델 정의
- 데이터베이스 스키마와 ORM 매핑

#### Services (비즈니스 로직)
- `server/services/`: 핵심 비즈니스 로직
- 데이터베이스 접근 및 외부 API 호출
- 재사용 가능한 서비스 단위

#### Controllers (요청 처리)
- `server/controllers/`: HTTP 요청 처리
- 요청 검증 및 응답 생성
- Service 레이어 호출

#### Routes (라우팅)
- `server/routes/`: URL 라우팅 정의
- Blueprint를 사용한 모듈화

### 데이터 흐름

```
HTTP Request
    ↓
Routes (라우팅)
    ↓
Controllers (요청 처리)
    ↓
Services (비즈니스 로직)
    ↓
Models (데이터베이스)
    ↓
Response
```

## 📝 주요 파일 설명

### Models
- `base.py`: SQLAlchemy Base 클래스
- `database.py`: DB 연결 및 세션 관리
- `user_credential.py`: 사용자 인증 정보 모델
- `subscription.py`: 구독 정보 모델
- `test.py`: 테스트 기록 모델

### Services
- `pat_auth_service.py`: PAT 인증 및 검증
- `subscription_service.py`: 구독 관리 로직
- `polling_service.py`: PR Polling 로직
- `test_pipeline_service.py`: 테스트 파이프라인 실행
- `pr_analyzer_service.py`: PR 분석 및 시나리오 생성
- `browser_executor.py`: 브라우저 자동화 실행
- `vision_validator.py`: Vision API 검증
- `slack_notifier.py`: Slack 알림 전송
- `k8s_deployer.py`: 쿠버네티스 배포

### Controllers
- `subscription_controller.py`: 구독 관리 API
- `pat_controller.py`: PAT 검증 API
- `test_controller.py`: 테스트 기록 API

### Routes
- `api_routes.py`: REST API 라우트
- `webhook_routes.py`: GitHub Webhook 라우트

### Utils
- `crypto.py`: PAT 암호화/복호화

### Config
- 환경 변수 설정 및 상수 정의

## 🔄 기존 src/ 디렉토리와의 차이

### 변경 전 (src/)
```
src/
├── api_server.py          # 모든 것이 한 파일에
├── webhook_server.py
├── models.py
├── subscription_manager.py
└── ...
```

### 변경 후 (server/)
```
server/
├── models/               # 모델 분리
├── services/             # 서비스 분리
├── controllers/           # 컨트롤러 분리
├── routes/               # 라우팅 분리
└── ...
```

## ✅ 장점

1. **관심사 분리**: 각 레이어가 명확한 역할
2. **유지보수성**: 코드 수정 시 영향 범위가 명확
3. **테스트 용이성**: 각 레이어를 독립적으로 테스트 가능
4. **확장성**: 새로운 기능 추가 시 구조가 명확
5. **재사용성**: Service 레이어를 여러 곳에서 재사용 가능


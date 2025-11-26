# NightWatch Frontend

React + Vite + Tailwind CSS로 구현된 NightWatch 프론트엔드입니다.

## 🚀 실행 방법

### 1. 패키지 설치

```bash
npm install
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 편집:

```bash
VITE_API_URL=http://localhost:5001
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

### 4. 빌드

```bash
npm run build
```

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── App.jsx          # 메인 컴포넌트
│   ├── App.css
│   ├── index.css        # Tailwind CSS
│   └── main.jsx         # 진입점
├── public/
├── package.json
├── tailwind.config.js
└── vite.config.js
```

## 🔌 API 연동

백엔드 API 서버가 `http://localhost:5001`에서 실행 중이어야 합니다.

### 주요 기능

- 레포지토리 구독 추가/삭제
- 구독 목록 조회
- 테스트 기록 조회
- 실시간 상태 업데이트 (30초마다)

## 🎨 스타일링

Tailwind CSS를 사용하여 반응형 디자인을 구현했습니다.

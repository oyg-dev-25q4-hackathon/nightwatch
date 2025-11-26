# Frontend 빠른 시작

## 🚀 실행 방법

### 1. 패키지 설치

```bash
cd frontend
npm install
```

### 2. Tailwind CSS 설치 (필요한 경우)

```bash
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

### 3. 환경 변수 설정

`.env` 파일 생성:

```bash
echo "VITE_API_URL=http://localhost:5001" > .env
```

### 4. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

## 📋 주요 기능

- ✅ 레포지토리 구독 추가 (PAT 입력)
- ✅ 구독 목록 조회
- ✅ 구독 해제
- ✅ 테스트 기록 조회
- ✅ 실시간 상태 업데이트 (30초마다)

## 🔧 문제 해결

### Tailwind CSS가 작동하지 않는 경우

```bash
# Tailwind CSS v3 설치
npm install -D tailwindcss@3 postcss autoprefixer

# 설정 파일 생성
npx tailwindcss init -p
```

### API 연결 오류

백엔드 서버가 실행 중인지 확인:

```bash
# 백엔드 서버 실행
cd ..
python main_with_polling.py
```


#!/bin/bash
# 프론트엔드 실행 스크립트

echo "🌐 NightWatch 프론트엔드 시작"
echo ""

cd frontend

# 패키지 확인
if [ ! -d "node_modules" ]; then
    echo "📦 패키지 설치 중..."
    npm install
fi

# 개발 서버 실행
echo "🚀 프론트엔드 서버 시작..."
npm run dev

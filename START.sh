#!/bin/bash
# NightWatch 프로젝트 실행 스크립트

echo "🌙 NightWatch 프로젝트 시작"
echo ""

# 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. 먼저 python3 -m venv venv를 실행하세요."
    exit 1
fi

source venv/bin/activate

# 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
fi

# 서버 실행
echo "🚀 백엔드 서버 시작..."
python main_with_polling.py

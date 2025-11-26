# main_with_polling.py
"""
메인 서버 - API 서버와 Polling 스케줄러를 함께 실행
"""
import os
import threading
from dotenv import load_dotenv
from server.app import app
from server.services.polling_scheduler import PollingScheduler
from server.config import POLLING_INTERVAL_MINUTES

load_dotenv()

def run_api_server():
    """API 서버 실행"""
    import warnings
    from server.config import API_PORT
    
    # Flask 개발 서버 경고 숨기기
    warnings.filterwarnings('ignore', message='.*development server.*')
    
    port = int(API_PORT)
    print(f"🌐 Starting API server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_polling_scheduler():
    """Polling 스케줄러 실행"""
    scheduler = PollingScheduler(interval_minutes=POLLING_INTERVAL_MINUTES)
    scheduler.start()
    
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()

if __name__ == "__main__":
    # 필수 디렉토리 생성
    from server.config import VIDEOS_DIR, SCREENSHOTS_DIR, REPORTS_DIR
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    print("🌙 NightWatch Server Starting...")
    print(f"Gemini API Key: {'✓ Set' if os.getenv('GEMINI_API_KEY') else '✗ Missing'}")
    print(f"Slack Token: {'✓ Set' if os.getenv('SLACK_TOKEN') else '✗ Missing'}")
    print(f"Encryption Key: {'✓ Set' if os.getenv('ENCRYPTION_KEY') else '✗ Missing (will generate)'}")
    
    # Polling 스케줄러를 별도 스레드에서 실행
    polling_thread = threading.Thread(target=run_polling_scheduler, daemon=True)
    polling_thread.start()
    
    # API 서버 실행 (메인 스레드)
    run_api_server()

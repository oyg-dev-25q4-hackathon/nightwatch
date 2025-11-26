# main_with_polling.py
"""
메인 서버 - API 서버와 Polling 스케줄러를 함께 실행
"""
import os
import threading
from dotenv import load_dotenv

# .env를 먼저 로드하여 이후 임포트되는 모듈들이 환경변수에 접근할 수 있게 함
load_dotenv()

from server.app import app
from server.services.polling_scheduler import PollingScheduler
from server.config import POLLING_INTERVAL_MINUTES

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
    
    vertex_ready = os.getenv('VERTEX_PROJECT_ID') and (
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or
        os.path.exists(os.path.join(os.path.dirname(__file__), 'credentials', 'vertex_service_account.json'))
    )
    print("🌙 NightWatch Server Starting...")
    print(f"Vertex Credentials: {'✓ Ready' if vertex_ready else '✗ Missing'}")
    print(f"Slack Token: {'✓ Set' if os.getenv('SLACK_TOKEN') else '✗ Missing'}")
    print(f"Encryption Key: {'✓ Set' if os.getenv('ENCRYPTION_KEY') else '✗ Missing (will generate)'}")
    
    # Polling 스케줄러를 별도 스레드에서 실행
    polling_thread = threading.Thread(target=run_polling_scheduler, daemon=True)
    polling_thread.start()
    
    # API 서버 실행 (메인 스레드)
    run_api_server()

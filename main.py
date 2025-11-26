# main.py
"""
메인 서버 - Webhook 방식
"""
import os
from dotenv import load_dotenv
from server.app import app
from server.models import init_db

load_dotenv()

if __name__ == "__main__":
    # 필수 디렉토리 생성
    from server.config import VIDEOS_DIR, SCREENSHOTS_DIR, REPORTS_DIR
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # 데이터베이스 초기화
    init_db()
    
    vertex_ready = os.getenv('VERTEX_PROJECT_ID') and (
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or
        os.path.exists(os.path.join(os.path.dirname(__file__), 'credentials', 'vertex_service_account.json'))
    )
    print("🌙 NightWatch Server Starting...")
    print(f"Vertex Credentials: {'✓ Ready' if vertex_ready else '✗ Missing'}")
    print(f"Slack Token: {'✓ Set' if os.getenv('SLACK_TOKEN') else '✗ Missing'}")
    
    # Flask 개발 서버 경고 숨기기
    import warnings
    warnings.filterwarnings('ignore', message='.*development server.*')
    
    app.run(host='0.0.0.0', port=5000, debug=True)

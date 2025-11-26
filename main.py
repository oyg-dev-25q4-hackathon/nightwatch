# main.py
import os
from dotenv import load_dotenv
from src.webhook_server import app

load_dotenv()

if __name__ == "__main__":
    # 필수 디렉토리 생성
    os.makedirs("videos", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    print("🌙 NightWatch Server Starting...")
    print(f"Gemini API Key: {'✓ Set' if os.getenv('GEMINI_API_KEY') else '✗ Missing'}")
    print(f"Slack Token: {'✓ Set' if os.getenv('SLACK_TOKEN') else '✗ Missing'}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


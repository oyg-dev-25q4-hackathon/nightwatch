# Config Package
import os

BASE_URL = os.getenv('BASE_URL', 'global.oliveyoung.com')
API_PORT = int(os.getenv('API_PORT', 5001))
POLLING_INTERVAL_MINUTES = int(os.getenv('POLLING_INTERVAL_MINUTES', 5))

# 출력 디렉토리 설정
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
VIDEOS_DIR = os.path.join(OUTPUT_DIR, 'videos')
SCREENSHOTS_DIR = os.path.join(OUTPUT_DIR, 'screenshots')
REPORTS_DIR = os.path.join(OUTPUT_DIR, 'reports')

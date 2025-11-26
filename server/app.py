# server/app.py
"""
Flask 애플리케이션 메인 파일
"""
from flask import Flask, jsonify
from flask_cors import CORS
from .routes.api_routes import api_bp
from .routes.webhook_routes import webhook_bp
from .models import init_db

def create_app():
    """Flask 앱 생성"""
    app = Flask(__name__)
    CORS(app)  # CORS 활성화
    
    # 데이터베이스 초기화
    init_db()
    
    # Blueprint 등록
    app.register_blueprint(api_bp)
    app.register_blueprint(webhook_bp)
    
    # 헬스 체크
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "service": "nightwatch-api"}), 200
    
    return app

app = create_app()

if __name__ == '__main__':
    from .config import API_PORT
    app.run(host='0.0.0.0', port=API_PORT, debug=True)


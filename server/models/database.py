# server/models/database.py
"""
데이터베이스 설정 및 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
import os

# 데이터베이스 경로
DB_PATH = os.getenv('DATABASE_URL', 'sqlite:///nightwatch.db')

# SQLAlchemy 엔진 생성
engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    # 순환 참조 방지를 위해 여기서 import
    from .base import Base
    # 모든 모델을 import하여 테이블이 등록되도록 함
    from .user_credential import UserCredential
    from .subscription import Subscription
    from .test import Test
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


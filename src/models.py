# src/models.py
"""
데이터베이스 모델 정의
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

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

class UserCredential(Base):
    """사용자 인증 정보 (PAT)"""
    __tablename__ = 'user_credentials'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)  # 사용자 식별자
    github_username = Column(String(255))
    encrypted_pat = Column(Text, nullable=False)  # 암호화된 PAT
    token_scopes = Column(JSON)  # 토큰 권한 목록
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified_at = Column(DateTime)  # 마지막 검증 시간
    
    # 관계
    subscriptions = relationship("Subscription", back_populates="credential")

class Subscription(Base):
    """레포지토리 구독 정보"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    user_credential_id = Column(Integer, ForeignKey('user_credentials.id'), nullable=False)
    repo_owner = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_full_name = Column(String(511), nullable=False, index=True)  # owner/repo
    auto_test = Column(Boolean, default=True)  # 자동 테스트 실행 여부
    slack_notify = Column(Boolean, default=True)  # Slack 알림 여부
    target_branches = Column(JSON)  # 특정 브랜치만 (null이면 모든 브랜치)
    test_options = Column(JSON)  # 테스트 옵션 (시나리오 수, 네임스페이스 등)
    is_active = Column(Boolean, default=True)  # 구독 활성화 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_polled_at = Column(DateTime)  # 마지막 Polling 시간
    
    # 관계
    credential = relationship("UserCredential", back_populates="subscriptions")
    tests = relationship("Test", back_populates="subscription")

class Test(Base):
    """테스트 기록"""
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    pr_number = Column(Integer, nullable=False)
    pr_url = Column(String(1023))
    repo_full_name = Column(String(511))
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    test_results = Column(JSON)  # 테스트 결과 상세
    report_path = Column(String(1023))  # 리포트 파일 경로
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계
    subscription = relationship("Subscription", back_populates="tests")

def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


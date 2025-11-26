# server/models/subscription.py
"""
레포지토리 구독 정보 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Subscription(Base):
    """레포지토리 구독 정보"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    user_credential_id = Column(Integer, ForeignKey('user_credentials.id'), nullable=True)  # Public 저장소는 PAT 불필요
    repo_owner = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_full_name = Column(String(511), nullable=False, index=True)
    auto_test = Column(Boolean, default=True)
    slack_notify = Column(Boolean, default=True)
    exclude_branches = Column(JSON)  # 제외할 브랜치 목록 (기본값: ['main'])
    test_options = Column(JSON)
    base_url = Column(String(511), nullable=True)  # 기본 배포 URL (예: global.oliveyoung.com) - PR URL은 pr-{번호}.{base_url} 형식으로 자동 생성
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_polled_at = Column(DateTime)
    
    # 관계
    credential = relationship("UserCredential", back_populates="subscriptions")
    tests = relationship("Test", back_populates="subscription")


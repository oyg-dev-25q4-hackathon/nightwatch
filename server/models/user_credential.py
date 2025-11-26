# server/models/user_credential.py
"""
사용자 인증 정보 모델 (PAT)
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class UserCredential(Base):
    """사용자 인증 정보 (PAT)"""
    __tablename__ = 'user_credentials'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    github_username = Column(String(255))
    encrypted_pat = Column(Text, nullable=False)
    token_scopes = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified_at = Column(DateTime)
    
    # 관계
    subscriptions = relationship("Subscription", back_populates="credential")


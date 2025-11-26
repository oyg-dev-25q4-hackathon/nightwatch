# server/models/test.py
"""
테스트 기록 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Test(Base):
    """테스트 기록"""
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    pr_number = Column(Integer, nullable=False)
    pr_url = Column(String(1023))
    repo_full_name = Column(String(511))
    status = Column(String(50), default='pending')
    test_results = Column(JSON)
    report_path = Column(String(1023))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계
    subscription = relationship("Subscription", back_populates="tests")


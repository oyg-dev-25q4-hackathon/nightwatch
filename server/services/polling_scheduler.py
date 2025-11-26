# server/services/polling_scheduler.py
"""
Polling 스케줄러
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
from .polling_service import PollingService
from ..models import init_db

class PollingScheduler:
    """Polling 스케줄러 클래스"""
    
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.polling_service = PollingService()
        self.is_running = False
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            print("⚠️ Scheduler is already running")
            return
        
        init_db()
        
        self.scheduler.add_job(
            func=self._poll_job,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='poll_prs',
            name='Poll PRs from subscribed repositories',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        print(f"✅ Polling scheduler started (interval: {self.interval_minutes} minutes)")
    
    def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        print("🛑 Polling scheduler stopped")
    
    def _poll_job(self):
        """실제 Polling 작업"""
        try:
            print(f"\n⏰ Running scheduled polling job...")
            self.polling_service.poll_all_subscriptions()
            print("✅ Polling job completed\n")
        except Exception as e:
            print(f"❌ Error in polling job: {str(e)}\n")


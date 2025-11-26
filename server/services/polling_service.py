# server/services/polling_service.py
"""
Polling 서비스 - 주기적으로 PR을 확인하고 테스트 실행
"""
import os
from datetime import datetime, timedelta
from github import Github
from ..models import Subscription, Test, get_db
from .subscription_service import SubscriptionService
from .pat_auth_service import PATAuthService
from .test_pipeline_service import TestPipelineService

class PollingService:
    """PR Polling 서비스"""
    
    def __init__(self):
        self.subscription_service = SubscriptionService()
        self.pat_auth = PATAuthService()
        self.test_pipeline = TestPipelineService()
        self.base_url = os.getenv('BASE_URL', 'global.oliveyoung.com')
    
    def poll_all_subscriptions(self):
        """모든 활성 구독에 대해 PR 확인 및 테스트 실행"""
        subscriptions = self.subscription_service.get_all_active_subscriptions()
        
        print(f"🔍 Polling {len(subscriptions)} active subscriptions...")
        
        for subscription in subscriptions:
            try:
                self._poll_subscription(subscription)
            except Exception as e:
                print(f"❌ Error polling subscription {subscription.id}: {str(e)}")
    
    def _poll_subscription(self, subscription: Subscription):
        """특정 구독에 대해 PR 확인"""
        print(f"  📦 Checking {subscription.repo_full_name}...")
        
        credential = self.pat_auth.get_credential_by_id(subscription.user_credential_id)
        if not credential:
            print(f"    ⚠️ No credential found for subscription {subscription.id}")
            return
        
        pat = self.pat_auth.get_decrypted_pat(credential.user_id)
        if not pat:
            print(f"    ⚠️ Failed to decrypt PAT for subscription {subscription.id}")
            return
        
        try:
            g = Github(pat)
            repo = g.get_repo(subscription.repo_full_name)
            
            since = subscription.last_polled_at
            if not since:
                since = datetime.utcnow() - timedelta(hours=1)
            
            pulls = repo.get_pulls(state='open', sort='updated', direction='desc')
            
            new_prs = []
            updated_prs = []
            
            for pr in pulls:
                if subscription.target_branches:
                    if not any(
                        pr.head.ref.startswith(branch.replace('*', '')) 
                        for branch in subscription.target_branches
                        if branch.endswith('*')
                    ) and pr.head.ref not in subscription.target_branches:
                        continue
                
                pr_updated = pr.updated_at.replace(tzinfo=None) if pr.updated_at else None
                
                if pr_updated and pr_updated > since:
                    if pr.created_at and pr.created_at.replace(tzinfo=None) > since:
                        new_prs.append(pr)
                    else:
                        updated_prs.append(pr)
            
            all_prs = new_prs + updated_prs
            if all_prs:
                print(f"    ✅ Found {len(all_prs)} PR(s) to test")
                for pr in all_prs:
                    self._run_test_for_pr(pr, subscription)
            else:
                print(f"    ℹ️ No new or updated PRs")
            
            self.subscription_service.update_last_polled(subscription.id)
            
        except Exception as e:
            print(f"    ❌ Error fetching PRs: {str(e)}")
    
    def _run_test_for_pr(self, pr, subscription: Subscription):
        """PR에 대해 테스트 실행"""
        pr_number = pr.number
        repo_name = subscription.repo_full_name
        branch_name = pr.head.ref
        
        print(f"    🚀 Running test for PR #{pr_number}...")
        
        db = next(get_db())
        try:
            recent_test = db.query(Test).filter(
                Test.subscription_id == subscription.id,
                Test.pr_number == pr_number,
                Test.status.in_(['pending', 'running'])
            ).first()
            
            if recent_test:
                print(f"      ℹ️ Test already running or pending for PR #{pr_number}")
                return
            
            test = Test(
                subscription_id=subscription.id,
                pr_number=pr_number,
                pr_url=pr.html_url,
                repo_full_name=repo_name,
                status='pending'
            )
            db.add(test)
            db.commit()
            test_id = test.id
            
        except Exception as e:
            db.rollback()
            print(f"      ❌ Failed to create test record: {str(e)}")
            return
        finally:
            db.close()
        
        try:
            pr_diff = self.test_pipeline.get_pr_diff(pr)
            
            db = next(get_db())
            try:
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.status = 'running'
                    db.commit()
            finally:
                db.close()
            
            result = self.test_pipeline.run_test_pipeline(pr, pr_diff, branch_name)
            
            db = next(get_db())
            try:
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.status = 'completed' if result['success'] else 'failed'
                    test.test_results = result.get('test_results')
                    test.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            
            print(f"      ✅ Test completed for PR #{pr_number}")
            
        except Exception as e:
            print(f"      ❌ Test failed for PR #{pr_number}: {str(e)}")
            
            db = next(get_db())
            try:
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.status = 'failed'
                    test.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()


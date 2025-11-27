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
        self.base_url = os.getenv('BASE_URL', 'localhost:5173')
    
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
        """특정 구독에 대해 PR 확인
        
        Returns:
            tuple: (감지된 PR 개수, 감지된 PR 목록, 테스트 미대상 PR 목록)
        """
        print(f"  📦 Checking {subscription.repo_full_name}...")
        
        # PAT가 있는 경우 사용, 없으면 Public 저장소로 간주
        pat = None
        if subscription.user_credential_id:
            credential = self.pat_auth.get_credential_by_id(subscription.user_credential_id)
            if credential:
                pat = self.pat_auth.get_decrypted_pat(credential.user_id)
        
        try:
            # PAT가 있으면 사용, 없으면 None으로 Public 저장소 접근
            if pat:
                g = Github(pat)
            else:
                # Public 저장소는 PAT 없이 접근 가능
                g = Github()
                print(f"    ℹ️ Using public API access (no PAT)")
            
            repo = g.get_repo(subscription.repo_full_name)
            
            since = subscription.last_polled_at
            # last_polled_at이 없으면 첫 polling이므로 모든 열린 PR을 확인 (30일 전까지)
            if not since:
                since = datetime.utcnow() - timedelta(days=30)
            
            pulls = repo.get_pulls(state='open', sort='updated', direction='desc')
            
            # PR 목록을 리스트로 변환 (제너레이터이므로)
            pulls_list = list(pulls)
            
            print(f"    📋 Found {len(pulls_list)} open PR(s) in repository")
            print(f"    📅 Last polled at: {subscription.last_polled_at}")
            print(f"    📅 Since: {since}")
            print(f"    🚫 Exclude branches: {subscription.exclude_branches or ['main']}")
            
            new_prs = []
            updated_prs = []
            non_target_prs = []  # 테스트 미대상 PR 목록
            
            # 제외할 브랜치 목록 (기본값: main)
            exclude_branches = subscription.exclude_branches or ['main']
            
            # DB에서 이미 테스트가 있는 PR 목록 확인
            db = next(get_db())
            try:
                existing_tests = db.query(Test).filter(
                    Test.subscription_id == subscription.id
                ).all()
                tested_pr_numbers = {test.pr_number for test in existing_tests}
            finally:
                db.close()
            
            for pr in pulls_list:
                pr_updated = pr.updated_at.replace(tzinfo=None) if pr.updated_at else None
                pr_created = pr.created_at.replace(tzinfo=None) if pr.created_at else None
                
                print(f"    🔍 Checking PR #{pr.number}: {pr.title[:50]}... (branch: {pr.head.ref})")
                
                # 테스트 대상 브랜치 확인: 정확히 "preview"인 경우만 테스트 대상
                is_test_target = pr.head.ref == "preview"
                
                # 제외할 브랜치인지 확인
                should_exclude = False
                
                for exclude_branch in exclude_branches:
                    # 와일드카드 패턴 지원 (예: "main*" -> "main", "main-dev" 등)
                    if exclude_branch.endswith('*'):
                        pattern = exclude_branch.replace('*', '')
                        if pr.head.ref.startswith(pattern):
                            should_exclude = True
                            break
                    # 정확한 매칭
                    elif pr.head.ref == exclude_branch:
                        should_exclude = True
                        break
                
                # 제외할 브랜치면 스킵
                if should_exclude:
                    print(f"      ⏭️ Skipping PR #{pr.number} (excluded branch: {pr.head.ref})")
                    continue
                
                # 테스트 대상이 아닌 경우 (preview 브랜치가 아닌 경우)
                if not is_test_target:
                    print(f"      ⏸️ PR #{pr.number} is not a test target (branch: {pr.head.ref}, required: 'preview')")
                    # 테스트 미대상 PR 목록에 추가
                    non_target_prs.append(pr)
                    continue
                
                # 첫 polling이거나 PR이 since 이후에 생성/업데이트된 경우
                is_first_polling = not subscription.last_polled_at
                
                if is_first_polling:
                    # 첫 polling: 모든 열린 PR을 새 PR로 처리
                    if pr_created:
                        new_prs.append(pr)
                        print(f"      ✅ Found PR #{pr.number} (first polling, branch: {pr.head.ref})")
                else:
                    # 이후 polling: since 이후 생성/업데이트된 PR 또는 테스트가 없는 PR
                    has_test = pr.number in tested_pr_numbers
                    
                    if pr_updated and pr_updated > since:
                        # PR이 since 이후에 업데이트됨
                        if pr_created and pr_created > since:
                            new_prs.append(pr)
                            print(f"      ✅ Found new PR #{pr.number} (branch: {pr.head.ref}, created: {pr_created})")
                        else:
                            updated_prs.append(pr)
                            print(f"      ✅ Found updated PR #{pr.number} (branch: {pr.head.ref}, updated: {pr_updated})")
                    elif not has_test:
                        # PR이 since 이전에 생성되었지만 테스트가 없는 경우
                        new_prs.append(pr)
                        print(f"      ✅ Found PR #{pr.number} (no test exists, branch: {pr.head.ref}, created: {pr_created})")
                    else:
                        print(f"      ⏭️ Skipping PR #{pr.number} (already tested, not updated since {since})")
            
            all_prs = new_prs + updated_prs
            detected_count = len(all_prs)
            
            # 감지된 PR 정보 수집 (테스트 대상)
            detected_pr_list = []
            for pr in all_prs:
                detected_pr_list.append({
                    'number': pr.number,
                    'title': pr.title,
                    'branch': pr.head.ref,
                    'url': pr.html_url,
                    'created_at': pr.created_at.isoformat() if pr.created_at else None,
                    'updated_at': pr.updated_at.isoformat() if pr.updated_at else None,
                    'is_test_target': True
                })
            
            # 테스트 미대상 PR 정보 수집
            non_target_pr_list = []
            for pr in non_target_prs:
                non_target_pr_list.append({
                    'number': pr.number,
                    'title': pr.title,
                    'branch': pr.head.ref,
                    'url': pr.html_url,
                    'created_at': pr.created_at.isoformat() if pr.created_at else None,
                    'updated_at': pr.updated_at.isoformat() if pr.updated_at else None,
                    'is_test_target': False
                })
            
            if all_prs:
                print(f"    ✅ Found {len(all_prs)} PR(s) to test")
                # PR 감지 후 즉시 DB에 pending 상태로 저장
                for pr in all_prs:
                    self._create_test_record(pr, subscription)
                
                # 백그라운드에서 테스트 실행 (비동기)
                import threading
                for pr in all_prs:
                    thread = threading.Thread(
                        target=self._run_test_for_pr,
                        args=(pr, subscription),
                        daemon=True
                    )
                    thread.start()
                    print(f"      🚀 Started background test for PR #{pr.number}")
            else:
                print(f"    ℹ️ No new or updated PRs")
            
            self.subscription_service.update_last_polled(subscription.id)
            
            return detected_count, detected_pr_list, non_target_pr_list
            
        except Exception as e:
            error_msg = str(e)
            # Rate limit 에러 체크
            if '403' in error_msg or 'rate limit' in error_msg.lower() or 'RateLimitExceededException' in str(type(e).__name__):
                print(f"    ⚠️ Rate limit exceeded for {subscription.repo_full_name}")
                print(f"    💡 Tip: Add a PAT to increase rate limit from 60/hour to 5,000/hour")
                # Rate limit 에러를 명확하게 전달
                raise Exception(f"GitHub API rate limit exceeded. Please add a Personal Access Token (PAT) to increase the limit from 60/hour to 5,000/hour. Error: {error_msg}")
            else:
                print(f"    ❌ Error fetching PRs: {str(e)}")
                raise
    
    def _create_test_record(self, pr, subscription: Subscription):
        """PR에 대한 테스트 레코드 생성 (pending 상태)"""
        pr_number = pr.number
        repo_name = subscription.repo_full_name
        branch_name = pr.head.ref
        
        db = next(get_db())
        try:
            # 이미 실행 중이거나 대기 중인 테스트가 있는지 확인
            recent_test = db.query(Test).filter(
                Test.subscription_id == subscription.id,
                Test.pr_number == pr_number,
                Test.status.in_(['pending', 'running'])
            ).first()
            
            if recent_test:
                print(f"      ℹ️ Test already exists for PR #{pr_number} (status: {recent_test.status}), skipping")
                return recent_test.id
            
            # 완료된 테스트가 있는지 확인
            completed_test = db.query(Test).filter(
                Test.subscription_id == subscription.id,
                Test.pr_number == pr_number,
                Test.status.in_(['completed', 'failed'])
            ).order_by(Test.created_at.desc()).first()
            
            if completed_test:
                print(f"      ℹ️ Test already exists for PR #{pr_number} (status: {completed_test.status}), creating new test")
            
            test = Test(
                subscription_id=subscription.id,
                pr_number=pr_number,
                pr_title=pr.title,
                pr_url=pr.html_url,
                branch_name=branch_name,
                repo_full_name=repo_name,
                status='pending'
            )
            db.add(test)
            db.commit()
            test_id = test.id
            print(f"      ✅ Created test record for PR #{pr_number} (ID: {test_id}, status: pending)")
            return test_id
            
        except Exception as e:
            db.rollback()
            print(f"      ❌ Failed to create test record: {str(e)}")
            return None
        finally:
            db.close()
    
    def _run_test_for_pr(self, pr, subscription: Subscription):
        """PR에 대해 테스트 실행 (백그라운드에서 실행)"""
        pr_number = pr.number
        repo_name = subscription.repo_full_name
        branch_name = pr.head.ref
        
        print(f"    🚀 Running test for PR #{pr_number} in background...")
        
        # 테스트 레코드 찾기
        db = next(get_db())
        try:
            test = db.query(Test).filter(
                Test.subscription_id == subscription.id,
                Test.pr_number == pr_number,
                Test.status == 'pending'
            ).order_by(Test.created_at.desc()).first()
            
            if not test:
                print(f"      ❌ Test record not found for PR #{pr_number}")
                return
            
            test_id = test.id
        except Exception as e:
            print(f"      ❌ Failed to find test record: {str(e)}")
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
            
            # preview 브랜치는 항상 preview-dev.oliveyoung.com 사용
            result = self.test_pipeline.run_test_pipeline(pr, pr_diff, branch_name, base_url=None)
            
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


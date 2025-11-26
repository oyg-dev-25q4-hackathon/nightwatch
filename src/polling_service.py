# src/polling_service.py
"""
Polling 서비스 - 주기적으로 PR을 확인하고 테스트 실행
"""
import os
from datetime import datetime, timedelta
from github import Github
from typing import List, Dict
from .subscription_manager import SubscriptionManager
from .pat_auth import PATAuth
from .models import Subscription, Test, get_db
# run_test_pipeline과 get_pr_diff는 webhook_server에서 import
# 순환 참조를 피하기 위해 직접 구현하거나 함수를 별도 모듈로 분리
from .pr_analyzer import PRAnalyzer
from .browser_executor import BrowserExecutor
from .vision_validator import VisionValidator
from .slack_notifier import SlackNotifier
from .k8s_deployer import K8sDeployer

class PollingService:
    """PR Polling 서비스"""
    
    def __init__(self):
        self.subscription_manager = SubscriptionManager()
        self.pat_auth = PATAuth()
        self.base_url = os.getenv('BASE_URL', 'global.oliveyoung.com')
    
    def poll_all_subscriptions(self):
        """모든 활성 구독에 대해 PR 확인 및 테스트 실행"""
        subscriptions = self.subscription_manager.get_all_active_subscriptions()
        
        print(f"🔍 Polling {len(subscriptions)} active subscriptions...")
        
        for subscription in subscriptions:
            try:
                self._poll_subscription(subscription)
            except Exception as e:
                print(f"❌ Error polling subscription {subscription.id}: {str(e)}")
    
    def _poll_subscription(self, subscription: Subscription):
        """특정 구독에 대해 PR 확인"""
        print(f"  📦 Checking {subscription.repo_full_name}...")
        
        # PAT 복호화
        credential = self.pat_auth.get_credential_by_id(subscription.user_credential_id)
        if not credential:
            print(f"    ⚠️ No credential found for subscription {subscription.id}")
            return
        
        pat = self.pat_auth.get_decrypted_pat(credential.user_id)
        if not pat:
            print(f"    ⚠️ Failed to decrypt PAT for subscription {subscription.id}")
            return
        
        # GitHub API로 PR 목록 조회
        try:
            g = Github(pat)
            repo = g.get_repo(subscription.repo_full_name)
            
            # 마지막 Polling 이후의 PR 조회
            since = subscription.last_polled_at
            if not since:
                # 첫 Polling인 경우 최근 1시간 이내의 PR만
                since = datetime.utcnow() - timedelta(hours=1)
            
            # PR 목록 조회
            pulls = repo.get_pulls(state='open', sort='updated', direction='desc')
            
            new_prs = []
            updated_prs = []
            
            for pr in pulls:
                # 브랜치 필터 확인
                if subscription.target_branches:
                    if not any(
                        pr.head.ref.startswith(branch.replace('*', '')) 
                        for branch in subscription.target_branches
                        if branch.endswith('*')
                    ) and pr.head.ref not in subscription.target_branches:
                        continue
                
                # 새 PR 또는 업데이트된 PR 확인
                pr_updated = pr.updated_at.replace(tzinfo=None) if pr.updated_at else None
                
                if pr_updated and pr_updated > since:
                    if pr.created_at and pr.created_at.replace(tzinfo=None) > since:
                        new_prs.append(pr)
                    else:
                        updated_prs.append(pr)
            
            # 새 PR 또는 업데이트된 PR이 있으면 테스트 실행
            all_prs = new_prs + updated_prs
            if all_prs:
                print(f"    ✅ Found {len(all_prs)} PR(s) to test")
                for pr in all_prs:
                    self._run_test_for_pr(pr, subscription)
            else:
                print(f"    ℹ️ No new or updated PRs")
            
            # 마지막 Polling 시간 업데이트
            self.subscription_manager.update_last_polled(subscription.id)
            
        except Exception as e:
            print(f"    ❌ Error fetching PRs: {str(e)}")
    
    def _run_test_for_pr(self, pr, subscription: Subscription):
        """PR에 대해 테스트 실행"""
        pr_number = pr.number
        repo_name = subscription.repo_full_name
        branch_name = pr.head.ref
        
        print(f"    🚀 Running test for PR #{pr_number}...")
        
        # 이미 테스트 중이거나 최근에 테스트한 PR인지 확인
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
            
            # 테스트 기록 생성
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
        
        # 백그라운드에서 테스트 실행 (비동기)
        try:
            # PR diff 가져오기
            pr_diff = self._get_pr_diff(pr)
            
            # 테스트 상태 업데이트
            db = next(get_db())
            try:
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.status = 'running'
                    db.commit()
            finally:
                db.close()
            
            # 테스트 파이프라인 실행
            self._run_test_pipeline(pr, pr_diff, branch_name)
            
            # 테스트 완료 상태 업데이트
            db = next(get_db())
            try:
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.status = 'completed'
                    test.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            
            print(f"      ✅ Test completed for PR #{pr_number}")
            
        except Exception as e:
            print(f"      ❌ Test failed for PR #{pr_number}: {str(e)}")
            
            # 테스트 실패 상태 업데이트
            db = next(get_db())
            try:
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    test.status = 'failed'
                    test.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
    
    def _get_pr_diff(self, pr):
        """PR의 변경사항 가져오기"""
        files = pr.get_files()
        diff_content = []
        
        for file in files:
            diff_content.append({
                'filename': file.filename,
                'status': file.status,
                'patch': file.patch if hasattr(file, 'patch') else None
            })
        
        return diff_content
    
    def _run_test_pipeline(self, pr, pr_diff, branch_name):
        """테스트 파이프라인 실행 (webhook_server의 run_test_pipeline과 동일)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pr_number = pr.number
        
        try:
            # 1. 쿠버네티스에 PR 배포
            print(f"      🚀 Deploying PR #{pr_number} to Kubernetes...")
            k8s_deployer = K8sDeployer(base_domain=self.base_url)
            repo_name = pr.base.repo.full_name
            
            deployment_info = k8s_deployer.deploy_pr(
                pr_number=pr_number,
                repo_name=repo_name,
                branch_name=branch_name
            )
            
            pr_url = deployment_info['url']
            pr_full_url = deployment_info['full_url']
            
            print(f"      ✅ PR deployed to: {pr_full_url}")
            
            # 2. PR 분석 및 시나리오 생성
            print(f"      📝 Analyzing PR with Gemini...")
            analyzer = PRAnalyzer(base_url=self.base_url)
            scenarios = analyzer.analyze_and_generate_scenarios(pr_diff, pr_url=pr_url)
            
            print(f"      ✓ Generated {len(scenarios)} test scenarios")
            
            # 3. Browser MCP를 사용하여 브라우저 테스트 실행
            print(f"      🌐 Executing browser tests with Browser MCP...")
            executor = BrowserExecutor(
                video_dir=f"videos/test_{timestamp}",
                use_mcp=True,
                base_url=self.base_url
            )
            test_results = []
            
            for scenario in scenarios:
                result = executor.execute_scenario(scenario, pr_url=pr_url)
                test_results.append(result)
            
            # 4. Vision API로 검증
            print(f"      👁️ Validating with Gemini Vision...")
            validator = VisionValidator()
            
            for result in test_results:
                if result['success'] and result.get('screenshot'):
                    validation = validator.validate_screenshot(
                        result['screenshot'],
                        result['expected_result']
                    )
                    result['validation'] = validation
            
            executor.close()
            
            # 5. 리포트 생성 및 슬랙 알림
            print(f"      📤 Sending Slack notification...")
            notifier = SlackNotifier()
            notifier.send_test_report(pr, test_results, timestamp, pr_url=pr_full_url)
            
            print(f"      ✅ Test pipeline completed!")
            
        except Exception as e:
            print(f"      ❌ Pipeline error: {str(e)}")
            # 에러도 슬랙으로 알림
            try:
                notifier = SlackNotifier()
                notifier.send_error_notification(pr, str(e))
            except:
                pass
            
            # 배포 정리 (에러 발생 시)
            try:
                k8s_deployer = K8sDeployer(base_domain=self.base_url)
                k8s_deployer.cleanup_pr(pr_number)
            except:
                pass


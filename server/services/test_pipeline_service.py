# server/services/test_pipeline_service.py
"""
테스트 파이프라인 실행 서비스
"""
import os
import sys
from datetime import datetime
from .k8s_deployer import K8sDeployer
from .local_deployer import LocalDeployer
from .pr_analyzer_service import PRAnalyzerService
from .browser_executor import BrowserExecutor
from .vision_validator import VisionValidator
from .slack_notifier import SlackNotifier

class TestPipelineService:
    """테스트 파이프라인 서비스"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('BASE_URL', 'global.oliveyoung.com')
    
    def run_test_pipeline(self, pr, pr_diff, branch_name, base_url=None):
        """
        테스트 파이프라인 실행
        
        Args:
            pr: GitHub PR 객체
            pr_diff: PR diff 정보
            branch_name: 브랜치 이름
            base_url: 구독에 저장된 기본 URL (예: global.oliveyoung.com) - PR URL은 pr-{번호}.{base_url} 형식으로 자동 생성
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pr_number = pr.number
        
        try:
            # 1. PR 배포 URL 결정
            # 우선순위: base_url (구독에 저장된 기본 URL) > 로컬 배포 > K8s 배포 > skip
            skip_deployment = False  # 기본값 설정
            
            if base_url:
                # 구독에 저장된 기본 URL로 PR URL 자동 생성
                # pr-{번호}.{base_url} 형식
                # https://, http://, 포트 번호 제거
                base_url_clean = base_url.replace('https://', '').replace('http://', '').strip('/')
                # 포트 번호 제거 (예: global.oliveyoung.com:8080 -> global.oliveyoung.com)
                if ':' in base_url_clean:
                    base_url_clean = base_url_clean.split(':')[0]
                pr_url = f"pr-{pr_number}.{base_url_clean}"
                pr_full_url = f"https://{pr_url}"
                skip_deployment = True  # 배포는 이미 되어 있다고 가정
                print(f"🌐 Using base URL from subscription: {base_url}")
                print(f"   ✅ Generated PR URL: {pr_full_url}")
            else:
                # 배포 URL이 없으면 배포 모드에 따라 배포
                deployment_mode = os.getenv('DEPLOYMENT_MODE', 'local').lower()  # 'local', 'k8s', 'skip'
                
                if deployment_mode == 'skip':
                    # 배포 건너뛰기: 기존 프로덕션 URL 사용 (PR 변경사항 반영 안됨)
                    print(f"ℹ️ Skipping deployment (DEPLOYMENT_MODE=skip)")
                    print(f"   ⚠️ Warning: PR changes will not be reflected in tests!")
                    print(f"   Using production URL: {self.base_url}")
                    pr_url = self.base_url
                    pr_full_url = f"https://{self.base_url}"
                    skip_deployment = True
                elif deployment_mode == 'local':
                    # 로컬에서 PR 브랜치 체크아웃 및 실행
                    print(f"🚀 Deploying PR #{pr_number} locally...")
                    local_deployer = LocalDeployer(base_domain=self.base_url)
                    repo_name = pr.base.repo.full_name
                    repo_url = pr.base.repo.clone_url  # GitHub clone URL
                    
                    deployment_info = local_deployer.deploy_pr(
                        pr_number=pr_number,
                        repo_name=repo_name,
                        branch_name=branch_name,
                        repo_url=repo_url
                    )
                    
                    pr_url = deployment_info['url']  # localhost:8001
                    pr_full_url = deployment_info['full_url']  # http://localhost:8001
                    skip_deployment = False
                    
                    print(f"✅ PR deployed locally to: {pr_full_url}")
                else:  # 'k8s'
                    # 실제 Kubernetes 배포
                    print(f"🚀 Deploying PR #{pr_number} to Kubernetes...")
                    k8s_deployer = K8sDeployer(base_domain=self.base_url)
                    repo_name = pr.base.repo.full_name
                    
                    deployment_info = k8s_deployer.deploy_pr(
                        pr_number=pr_number,
                        repo_name=repo_name,
                        branch_name=branch_name
                    )
                    
                    pr_url = deployment_info['url']
                    pr_full_url = deployment_info['full_url']
                    skip_deployment = False
                    
                    print(f"✅ PR deployed to: {pr_full_url}")
            
            # 2. PR 분석 및 시나리오 생성
            print("📝 Analyzing PR with Gemini...")
            analyzer = PRAnalyzerService(base_url=self.base_url)
            # 배포를 건너뛴 경우 pr_url=None으로 전달하여 base_url 사용
            test_pr_url_for_analysis = pr_url if not skip_deployment else None
            scenarios = analyzer.analyze_and_generate_scenarios(pr_diff, pr_url=test_pr_url_for_analysis)
            
            print(f"✓ Generated {len(scenarios)} test scenarios")
            
            # 3. Browser MCP를 사용하여 브라우저 테스트 실행
            print("🌐 Executing browser tests with Browser MCP...")
            from ..config import VIDEOS_DIR
            os.makedirs(VIDEOS_DIR, exist_ok=True)
            executor = BrowserExecutor(
                video_dir=os.path.join(VIDEOS_DIR, f"test_{timestamp}"),
                use_mcp=True,
                base_url=self.base_url
            )
            test_results = []
            
            for scenario in scenarios:
                # 배포를 건너뛴 경우 pr_url=None으로 전달하여 base_url 사용
                test_pr_url = pr_url if not skip_deployment else None
                result = executor.execute_scenario(scenario, pr_url=test_pr_url)
                test_results.append(result)
            
            # 4. Vision API로 검증
            print("👁️ Validating with Gemini Vision...")
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
            print("📤 Sending Slack notification...")
            notifier = SlackNotifier()
            notifier.send_test_report(pr, test_results, timestamp, pr_url=pr_full_url)
            
            print("✅ Test pipeline completed!")
            
            return {
                'success': True,
                'test_results': test_results,
                'pr_url': pr_full_url
            }
            
        except Exception as e:
            print(f"❌ Pipeline error: {str(e)}")
            # 에러도 슬랙으로 알림
            try:
                notifier = SlackNotifier()
                notifier.send_error_notification(pr, str(e))
            except:
                pass
            
            # 배포 정리 (에러 발생 시, 배포를 건너뛴 경우는 정리 불필요)
            if not skip_deployment:
                try:
                    k8s_deployer = K8sDeployer(base_domain=self.base_url)
                    k8s_deployer.cleanup_pr(pr_number)
                except:
                    pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pr_diff(self, pr):
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
    
    def rerun_scenario(self, scenario, pr_url=None):
        """
        특정 시나리오만 재실행
        
        Args:
            scenario: 재실행할 시나리오 딕셔너리
            pr_url: PR 배포 URL (선택사항)
        
        Returns:
            dict: 시나리오 실행 결과
        """
        from ..config import VIDEOS_DIR
        import os
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        
        executor = BrowserExecutor(
            video_dir=os.path.join(VIDEOS_DIR, f"rerun_{timestamp}"),
            use_mcp=True,
            base_url=self.base_url
        )
        
        try:
            # 시나리오 실행
            result = executor.execute_scenario(scenario, pr_url=pr_url)
            
            # Vision API로 검증
            if result['success'] and result.get('screenshot'):
                validator = VisionValidator()
                validation = validator.validate_screenshot(
                    result['screenshot'],
                    result.get('expected_result', '')
                )
                result['validation'] = validation
            
            return result
        finally:
            executor.close()


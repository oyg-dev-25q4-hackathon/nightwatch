# server/services/test_pipeline_service.py
"""
테스트 파이프라인 실행 서비스
"""
import os
from datetime import datetime
from .k8s_deployer import K8sDeployer
from .pr_analyzer_service import PRAnalyzerService
from .browser_executor import BrowserExecutor
from .vision_validator import VisionValidator
from .slack_notifier import SlackNotifier

class TestPipelineService:
    """테스트 파이프라인 서비스"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('BASE_URL', 'global.oliveyoung.com')
    
    def run_test_pipeline(self, pr, pr_diff, branch_name):
        """테스트 파이프라인 실행"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pr_number = pr.number
        
        try:
            # 1. 쿠버네티스에 PR 배포
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
            
            print(f"✅ PR deployed to: {pr_full_url}")
            
            # 2. PR 분석 및 시나리오 생성
            print("📝 Analyzing PR with Gemini...")
            analyzer = PRAnalyzerService(base_url=self.base_url)
            scenarios = analyzer.analyze_and_generate_scenarios(pr_diff, pr_url=pr_url)
            
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
                result = executor.execute_scenario(scenario, pr_url=pr_url)
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
            
            # 배포 정리 (에러 발생 시)
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


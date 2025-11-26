# src/k8s_deployer.py
import os
import subprocess
import time
import logging

logger = logging.getLogger(__name__)

class K8sDeployer:
    """쿠버네티스에 PR을 배포하는 클래스"""
    
    def __init__(self, base_domain=None):
        """
        Args:
            base_domain: 기본 도메인 (기본값: global.oliveyoung.com)
        """
        self.base_domain = base_domain or os.getenv('BASE_DOMAIN', 'global.oliveyoung.com')
        self.namespace = os.getenv('K8S_NAMESPACE', 'default')
        self.deployment_prefix = os.getenv('DEPLOYMENT_PREFIX', 'pr-preview')
    
    def deploy_pr(self, pr_number, repo_name, branch_name):
        """
        PR을 쿠버네티스에 배포
        
        Args:
            pr_number: PR 번호
            repo_name: 저장소 이름 (예: 'owner/repo')
            branch_name: 브랜치 이름
            
        Returns:
            dict: 배포 정보 {'url': 'pr-123.global.oliveyoung.com', 'status': 'deployed'}
        """
        try:
            print(f"🚀 Deploying PR #{pr_number} to Kubernetes...")
            
            # PR URL 생성
            pr_url = f"pr-{pr_number}.{self.base_domain}"
            
            # 쿠버네티스 배포 명령 실행
            # 실제 구현은 환경에 따라 다를 수 있음
            deployment_name = f"{self.deployment_prefix}-{pr_number}"
            
            # 예시: kubectl을 사용한 배포
            # 실제로는 ArgoCD, Helm, 또는 다른 배포 도구를 사용할 수 있음
            deploy_result = self._execute_deployment(
                deployment_name=deployment_name,
                pr_number=pr_number,
                repo_name=repo_name,
                branch_name=branch_name,
                pr_url=pr_url
            )
            
            if deploy_result['success']:
                print(f"✅ PR #{pr_number} deployed successfully")
                print(f"   URL: https://{pr_url}")
                
                # 배포가 완료될 때까지 대기
                self._wait_for_deployment_ready(pr_url)
                
                return {
                    'url': pr_url,
                    'full_url': f"https://{pr_url}",
                    'status': 'deployed',
                    'deployment_name': deployment_name
                }
            else:
                raise Exception(f"Deployment failed: {deploy_result.get('error')}")
                
        except Exception as e:
            logger.error(f"K8s deployment error: {e}")
            raise
    
    def _execute_deployment(self, deployment_name, pr_number, repo_name, branch_name, pr_url):
        """
        실제 배포 명령 실행
        이 부분은 실제 쿠버네티스 환경에 맞게 수정 필요
        """
        try:
            # 예시 1: kubectl을 사용한 직접 배포
            # kubectl_cmd = [
            #     'kubectl', 'create', 'deployment',
            #     deployment_name,
            #     f'--image=your-registry/app:pr-{pr_number}',
            #     f'--namespace={self.namespace}'
            # ]
            # subprocess.run(kubectl_cmd, check=True)
            
            # 예시 2: Helm을 사용한 배포
            # helm_cmd = [
            #     'helm', 'upgrade', '--install',
            #     deployment_name,
            #     './helm-chart',
            #     '--set', f'image.tag=pr-{pr_number}',
            #     '--set', f'ingress.host={pr_url}',
            #     f'--namespace={self.namespace}'
            # ]
            # subprocess.run(helm_cmd, check=True)
            
            # 예시 3: ArgoCD를 사용한 배포
            # argocd_cmd = [
            #     'argocd', 'app', 'create',
            #     f'--name={deployment_name}',
            #     f'--repo={repo_name}',
            #     f'--revision={branch_name}',
            #     f'--dest-server=https://kubernetes.default.svc',
            #     f'--dest-namespace={self.namespace}'
            # ]
            # subprocess.run(argocd_cmd, check=True)
            
            # 현재는 모의 배포 (실제 환경에서는 위의 방법 중 하나를 사용)
            print(f"   [MOCK] Creating deployment: {deployment_name}")
            print(f"   [MOCK] PR URL will be: https://{pr_url}")
            
            return {'success': True}
            
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _wait_for_deployment_ready(self, pr_url, max_wait_seconds=300):
        """
        배포가 완료되고 서비스가 준비될 때까지 대기
        
        Args:
            pr_url: PR URL
            max_wait_seconds: 최대 대기 시간 (기본 5분)
        """
        print(f"⏳ Waiting for deployment to be ready...")
        
        # 실제로는 kubectl get pods 또는 HTTP 헬스체크를 사용
        # 예시:
        # for i in range(max_wait_seconds // 10):
        #     try:
        #         response = requests.get(f"https://{pr_url}/health", timeout=5)
        #         if response.status_code == 200:
        #             print(f"✅ Deployment is ready!")
        #             return
        #     except:
        #         pass
        #     time.sleep(10)
        
        # 현재는 모의 대기
        time.sleep(5)  # 실제로는 제거하고 위의 로직 사용
        print(f"✅ Deployment is ready!")
    
    def cleanup_pr(self, pr_number):
        """
        PR 배포 정리 (PR이 닫히거나 머지될 때)
        
        Args:
            pr_number: PR 번호
        """
        try:
            print(f"🧹 Cleaning up PR #{pr_number} deployment...")
            
            deployment_name = f"{self.deployment_prefix}-{pr_number}"
            
            # kubectl delete deployment {deployment_name} --namespace={self.namespace}
            # 또는 Helm/ArgoCD를 사용한 삭제
            
            print(f"   [MOCK] Deleting deployment: {deployment_name}")
            print(f"✅ PR #{pr_number} deployment cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            raise


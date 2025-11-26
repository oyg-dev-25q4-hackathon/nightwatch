# server/services/local_deployer.py
"""
로컬에서 PR 브랜치를 체크아웃하고 실행하는 배포기
해커톤 규모에서 Kubernetes 없이 PR 변경사항을 테스트하기 위한 간단한 방법
"""
import os
import sys
import subprocess
import shutil
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalDeployer:
    """로컬에서 PR 브랜치를 체크아웃하고 실행하는 클래스"""
    
    def __init__(self, base_domain=None, work_dir=None):
        """
        Args:
            base_domain: 기본 도메인 (기본값: global.oliveyoung.com)
            work_dir: 작업 디렉토리 (기본값: ./pr_deployments)
        """
        self.base_domain = base_domain or os.getenv('BASE_DOMAIN', 'global.oliveyoung.com')
        self.work_dir = Path(work_dir or os.getenv('PR_DEPLOYMENT_DIR', './pr_deployments'))
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.port_base = int(os.getenv('PR_PORT_BASE', '8000'))
    
    def deploy_pr(self, pr_number, repo_name, branch_name, repo_url=None):
        """
        PR 브랜치를 로컬에 체크아웃하고 실행
        
        Args:
            pr_number: PR 번호
            repo_name: 저장소 이름 (예: 'owner/repo')
            branch_name: 브랜치 이름
            repo_url: 저장소 URL (선택사항, 없으면 GitHub에서 자동 생성)
            
        Returns:
            dict: 배포 정보 {'url': 'localhost:8001', 'status': 'deployed', 'process': process}
        """
        try:
            print(f"🚀 Deploying PR #{pr_number} locally...")
            print(f"   Repository: {repo_name}")
            print(f"   Branch: {branch_name}")
            
            # 작업 디렉토리 생성
            pr_dir = self.work_dir / f"pr-{pr_number}"
            
            # 저장소 URL 생성
            if not repo_url:
                repo_url = f"https://github.com/{repo_name}.git"
            
            # 저장소 클론 또는 업데이트
            if pr_dir.exists():
                print(f"   📂 Updating existing checkout...")
                self._update_repo(pr_dir, branch_name)
            else:
                print(f"   📂 Cloning repository...")
                self._clone_repo(repo_url, pr_dir, branch_name)
            
            # 포트 할당
            port = self.port_base + pr_number
            
            # 서버 실행 (프로젝트 타입에 따라 다름)
            process = self._start_server(pr_dir, port, pr_number)
            
            # 서버가 준비될 때까지 대기
            self._wait_for_server_ready(port, max_wait_seconds=60)
            
            pr_url = f"localhost:{port}"
            pr_full_url = f"http://{pr_url}"
            
            print(f"✅ PR #{pr_number} deployed locally")
            print(f"   URL: {pr_full_url}")
            
            return {
                'url': pr_url,
                'full_url': pr_full_url,
                'status': 'deployed',
                'port': port,
                'process': process,
                'work_dir': str(pr_dir)
            }
            
        except Exception as e:
            logger.error(f"Local deployment error: {e}")
            raise
    
    def _clone_repo(self, repo_url, target_dir, branch_name):
        """저장소 클론"""
        try:
            # 깊은 클론 (shallow clone은 브랜치 체크아웃에 문제가 있을 수 있음)
            subprocess.run(
                ['git', 'clone', '--depth', '1', '--branch', branch_name, repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 브랜치가 없으면 전체 클론 후 체크아웃
            print(f"   ⚠️ Branch not found, cloning full repo...")
            subprocess.run(['git', 'clone', repo_url, str(target_dir)], check=True)
            subprocess.run(['git', 'checkout', branch_name], cwd=target_dir, check=True)
    
    def _update_repo(self, repo_dir, branch_name):
        """저장소 업데이트"""
        try:
            subprocess.run(['git', 'fetch', 'origin'], cwd=repo_dir, check=True)
            subprocess.run(['git', 'checkout', branch_name], cwd=repo_dir, check=True)
            subprocess.run(['git', 'pull', 'origin', branch_name], cwd=repo_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Update failed: {e}")
            raise
    
    def _start_server(self, pr_dir, port, pr_number):
        """
        프로젝트 타입에 따라 서버 실행
        - package.json이 있으면 npm/yarn 실행
        - requirements.txt가 있으면 Python 서버 실행
        - 그 외에는 간단한 HTTP 서버
        """
        # package.json 확인 (Node.js 프로젝트)
        if (pr_dir / 'package.json').exists():
            print(f"   📦 Detected Node.js project")
            # 의존성 설치 (처음만)
            if not (pr_dir / 'node_modules').exists():
                print(f"   📥 Installing dependencies...")
                if (pr_dir / 'yarn.lock').exists():
                    subprocess.run(['yarn', 'install'], cwd=pr_dir, check=True)
                else:
                    subprocess.run(['npm', 'install'], cwd=pr_dir, check=True)
            
            # 서버 실행
            env = os.environ.copy()
            env['PORT'] = str(port)
            # package.json의 scripts 확인
            package_json = (pr_dir / 'package.json').read_text()
            if 'dev' in package_json or 'start' in package_json:
                script = 'dev' if 'dev' in package_json else 'start'
                process = subprocess.Popen(
                    ['npm', 'run', script] if 'npm' not in package_json else ['yarn', script],
                    cwd=pr_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # 기본 서버 실행
                process = subprocess.Popen(
                    ['npx', 'serve', '-p', str(port), '.'],
                    cwd=pr_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            return process
        
        # requirements.txt 확인 (Python 프로젝트)
        elif (pr_dir / 'requirements.txt').exists():
            print(f"   🐍 Detected Python project")
            # 가상환경 생성 및 의존성 설치
            venv_dir = pr_dir / 'venv'
            venv_created = False
            if not venv_dir.exists():
                print(f"   📥 Creating virtual environment...")
                subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
                venv_created = True
            
            # 가상환경이 생성될 때까지 대기 (생성된 경우 더 길게 대기)
            import time
            wait_time = 3 if venv_created else 1
            time.sleep(wait_time)
            
            pip = venv_dir / 'bin' / 'pip' if os.name != 'nt' else venv_dir / 'Scripts' / 'pip.exe'
            python = venv_dir / 'bin' / 'python' if os.name != 'nt' else venv_dir / 'Scripts' / 'python.exe'
            
            # pip가 존재하는지 확인 (최대 5초까지 재시도)
            max_retries = 5
            retry_count = 0
            while not pip.exists() and retry_count < max_retries:
                print(f"   ⏳ Waiting for virtual environment to be ready... ({retry_count + 1}/{max_retries})")
                time.sleep(1)
                retry_count += 1
                # 경로 재확인
                pip = venv_dir / 'bin' / 'pip' if os.name != 'nt' else venv_dir / 'Scripts' / 'pip.exe'
            
            # pip가 여전히 없으면 시스템 pip 사용
            if not pip.exists():
                print(f"   ⚠️ Virtual environment pip not found, using system pip...")
                # 시스템 pip 경로 찾기 (pip3 우선)
                try:
                    import shutil
                    system_pip = shutil.which('pip3') or shutil.which('pip')
                    if system_pip:
                        pip = Path(system_pip)
                        # python도 pip3에 맞게 조정
                        python3 = shutil.which('python3') or sys.executable
                        python = Path(python3) if python3 else sys.executable
                        print(f"   ✅ Using system pip: {pip}")
                    else:
                        # 마지막 수단: python -m pip 사용
                        pip = None  # None으로 설정하면 python -m pip 사용
                        python = sys.executable
                        print(f"   ✅ Will use 'python -m pip'")
                except Exception as e:
                    print(f"   ⚠️ Could not find system pip, will use 'python -m pip': {e}")
                    pip = None
                    python = sys.executable
            
            print(f"   📥 Installing dependencies...")
            try:
                if pip is None:
                    # python -m pip 사용 (python3 우선)
                    python_cmd = str(python) if isinstance(python, Path) else python
                    subprocess.run([python_cmd, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=pr_dir, check=True)
                else:
                    # 절대 경로 사용
                    pip_abs = str(pip.resolve()) if hasattr(pip, 'resolve') else str(pip.absolute())
                    subprocess.run([pip_abs, 'install', '-r', 'requirements.txt'], cwd=pr_dir, check=True)
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install dependencies: {e}")
                print(f"   📋 pip 경로: {pip}")
                print(f"   📋 python 경로: {python}")
                print(f"   📋 작업 디렉토리: {pr_dir}")
                # pip3로 재시도
                if pip and 'pip3' not in str(pip):
                    print(f"   🔄 Retrying with pip3...")
                    try:
                        import shutil
                        pip3_path = shutil.which('pip3')
                        if pip3_path:
                            subprocess.run([pip3_path, 'install', '-r', 'requirements.txt'], cwd=pr_dir, check=True)
                            print(f"   ✅ Successfully installed with pip3")
                        else:
                            raise
                    except Exception as e2:
                        print(f"   ❌ pip3 also failed: {e2}")
                        raise e
                else:
                    raise
            
            # Flask/Django 등 확인
            if (pr_dir / 'app.py').exists() or (pr_dir / 'main.py').exists():
                app_file = 'app.py' if (pr_dir / 'app.py').exists() else 'main.py'
                env = os.environ.copy()
                env['PORT'] = str(port)
                process = subprocess.Popen(
                    [str(python), app_file],
                    cwd=pr_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # 간단한 HTTP 서버
                process = subprocess.Popen(
                    [str(python), '-m', 'http.server', str(port)],
                    cwd=pr_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            return process
        
        else:
            # 정적 파일 서버
            print(f"   📄 Detected static files, starting simple HTTP server...")
            process = subprocess.Popen(
                [sys.executable, '-m', 'http.server', str(port)],
                cwd=pr_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return process
    
    def _wait_for_server_ready(self, port, max_wait_seconds=60):
        """서버가 준비될 때까지 대기"""
        try:
            import requests
        except ImportError:
            print(f"   ⚠️ requests library not found, skipping server readiness check")
            time.sleep(5)  # 기본 대기
            return
        
        url = f"http://localhost:{port}"
        
        print(f"   ⏳ Waiting for server to be ready...")
        for i in range(max_wait_seconds):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code < 500:  # 4xx는 괜찮음 (서버는 실행 중)
                    print(f"   ✅ Server is ready!")
                    return
            except:
                pass
            time.sleep(1)
        
        print(f"   ⚠️ Server may not be ready, but continuing...")
    
    def cleanup_pr(self, pr_number):
        """
        PR 배포 정리 (프로세스 종료 및 디렉토리 삭제)
        
        Args:
            pr_number: PR 번호
        """
        try:
            print(f"🧹 Cleaning up PR #{pr_number} deployment...")
            
            pr_dir = self.work_dir / f"pr-{pr_number}"
            
            # 프로세스 종료는 별도로 관리 필요 (실제로는 프로세스 ID 저장 필요)
            # 여기서는 디렉토리만 삭제
            if pr_dir.exists():
                shutil.rmtree(pr_dir)
                print(f"   ✅ Cleaned up PR #{pr_number}")
            else:
                print(f"   ℹ️ No deployment found for PR #{pr_number}")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            raise


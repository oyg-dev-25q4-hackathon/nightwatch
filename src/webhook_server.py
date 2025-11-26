# src/webhook_server.py
from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from github import Github
from .pr_analyzer import PRAnalyzer
from .browser_executor import BrowserExecutor
from .vision_validator import VisionValidator
from .slack_notifier import SlackNotifier
from .k8s_deployer import K8sDeployer
import json
from datetime import datetime

app = Flask(__name__)

# 기본 웹사이트 URL 설정
BASE_URL = os.getenv('BASE_URL', 'global.oliveyoung.com')

def verify_signature(payload_body, signature_header):
    """GitHub Webhook 서명 검증"""
    if not signature_header:
        return False
    
    secret = os.getenv('GITHUB_WEBHOOK_SECRET', '').encode()
    hash_object = hmac.new(secret, msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "nightwatch"}), 200

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # 서명 검증
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    payload = request.json
    
    # PR 이벤트 처리
    action = payload.get('action')
    
    # PR이 닫히거나 머지될 때 배포 정리
    if action in ['closed', 'merged']:
        try:
            pr_number = payload['pull_request']['number']
            print(f"🧹 Cleaning up PR #{pr_number} deployment...")
            
            k8s_deployer = K8sDeployer(base_domain=BASE_URL)
            k8s_deployer.cleanup_pr(pr_number)
            
            return jsonify({"message": "Deployment cleaned up"}), 200
        except Exception as e:
            print(f"❌ Cleanup error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # PR이 열렸거나 업데이트될 때만 테스트 실행
    if action not in ['opened', 'synchronize']:
        return jsonify({"message": "Ignored event"}), 200
    
    try:
        pr_number = payload['pull_request']['number']
        repo_name = payload['repository']['full_name']
        branch_name = payload['pull_request']['head']['ref']
        
        print(f"🔍 Processing PR #{pr_number} in {repo_name}")
        
        # PR 정보 가져오기
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # PR diff 가져오기
        pr_diff = get_pr_diff(pr)
        
        # 테스트 파이프라인 실행
        run_test_pipeline(pr, pr_diff, branch_name)
        
        return jsonify({"message": "Test pipeline started"}), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_pr_diff(pr):
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

def run_test_pipeline(pr, pr_diff, branch_name):
    """테스트 파이프라인 실행"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pr_number = pr.number
    
    try:
        # 1. 쿠버네티스에 PR 배포
        print(f"🚀 Deploying PR #{pr_number} to Kubernetes...")
        k8s_deployer = K8sDeployer(base_domain=BASE_URL)
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
        analyzer = PRAnalyzer(base_url=BASE_URL)
        scenarios = analyzer.analyze_and_generate_scenarios(pr_diff, pr_url=pr_url)
        
        print(f"✓ Generated {len(scenarios)} test scenarios")
        
        # 3. Browser MCP를 사용하여 브라우저 테스트 실행
        print("🌐 Executing browser tests with Browser MCP...")
        executor = BrowserExecutor(
            video_dir=f"videos/test_{timestamp}",
            use_mcp=True,
            base_url=BASE_URL
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
        
        # 6. (선택사항) PR이 닫히거나 머지될 때 배포 정리
        # 이 부분은 별도의 webhook 핸들러에서 처리할 수 있음
        
    except Exception as e:
        print(f"❌ Pipeline error: {str(e)}")
        # 에러도 슬랙으로 알림
        notifier = SlackNotifier()
        notifier.send_error_notification(pr, str(e))
        
        # 배포 정리 (에러 발생 시)
        try:
            k8s_deployer = K8sDeployer(base_domain=BASE_URL)
            k8s_deployer.cleanup_pr(pr_number)
        except:
            pass


# server/routes/webhook_routes.py
"""
Webhook 라우트 정의
"""
from flask import Blueprint, request, jsonify
import hmac
import hashlib
import os
from github import Github
from ..services.test_pipeline_service import TestPipelineService
from ..services.k8s_deployer import K8sDeployer
from ..config import BASE_URL

webhook_bp = Blueprint('webhook', __name__)

def verify_signature(payload_body, signature_header):
    """GitHub Webhook 서명 검증"""
    if not signature_header:
        return False
    
    secret = os.getenv('GITHUB_WEBHOOK_SECRET', '').encode()
    hash_object = hmac.new(secret, msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

@webhook_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """GitHub Webhook 처리"""
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    payload = request.json
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
        
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        test_pipeline = TestPipelineService(base_url=BASE_URL)
        pr_diff = test_pipeline.get_pr_diff(pr)
        
        test_pipeline.run_test_pipeline(pr, pr_diff, branch_name)
        
        return jsonify({"message": "Test pipeline started"}), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


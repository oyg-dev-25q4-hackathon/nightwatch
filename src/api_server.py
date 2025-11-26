# src/api_server.py
"""
API 서버 - 레포지토리 구독 관리 API
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from .subscription_manager import SubscriptionManager
from .pat_auth import PATAuth
from .models import init_db, Test, get_db, Subscription
from datetime import datetime

app = Flask(__name__)
CORS(app)  # CORS 활성화 (React UI와 통신용)

# 기본 웹사이트 URL 설정
BASE_URL = os.getenv('BASE_URL', 'global.oliveyoung.com')

# 모듈 초기화
subscription_manager = SubscriptionManager()
pat_auth = PATAuth()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "nightwatch-api"}), 200

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """구독 목록 조회"""
    user_id = request.args.get('user_id', 'default')  # 기본값, 실제로는 인증에서 가져옴
    
    try:
        subscriptions = subscription_manager.get_subscriptions(user_id)
        return jsonify({
            'success': True,
            'subscriptions': subscriptions
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    """레포지토리 구독 생성"""
    data = request.json
    
    user_id = data.get('user_id', 'default')  # 기본값
    repo_full_name = data.get('repo_full_name')
    pat = data.get('pat')
    auto_test = data.get('auto_test', True)
    slack_notify = data.get('slack_notify', True)
    target_branches = data.get('target_branches')
    test_options = data.get('test_options', {})
    
    if not repo_full_name or not pat:
        return jsonify({
            'success': False,
            'error': 'repo_full_name and pat are required'
        }), 400
    
    try:
        result = subscription_manager.create_subscription(
            user_id=user_id,
            repo_full_name=repo_full_name,
            pat=pat,
            auto_test=auto_test,
            slack_notify=slack_notify,
            target_branches=target_branches,
            test_options=test_options
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'subscription_id': result['subscription_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/subscriptions/<int:subscription_id>', methods=['GET'])
def get_subscription(subscription_id):
    """특정 구독 정보 조회"""
    user_id = request.args.get('user_id', 'default')
    
    try:
        subscriptions = subscription_manager.get_subscriptions(user_id)
        subscription = next((s for s in subscriptions if s['id'] == subscription_id), None)
        
        if subscription:
            return jsonify({
                'success': True,
                'subscription': subscription
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Subscription not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/subscriptions/<int:subscription_id>', methods=['DELETE'])
def delete_subscription(subscription_id):
    """구독 삭제"""
    user_id = request.args.get('user_id', 'default')
    
    try:
        success = subscription_manager.delete_subscription(subscription_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Subscription deleted'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Subscription not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pat/verify', methods=['POST'])
def verify_pat():
    """PAT 검증"""
    data = request.json
    pat = data.get('pat')
    
    if not pat:
        return jsonify({
            'success': False,
            'error': 'pat is required'
        }), 400
    
    try:
        result = pat_auth.verify_pat(pat)
        
        if result['valid']:
            return jsonify({
                'success': True,
                'username': result['username'],
                'user_id': result.get('user_id')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Invalid token')
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pat/check-repo', methods=['POST'])
def check_repo_access():
    """레포지토리 접근 권한 확인"""
    data = request.json
    pat = data.get('pat')
    repo_full_name = data.get('repo_full_name')
    
    if not pat or not repo_full_name:
        return jsonify({
            'success': False,
            'error': 'pat and repo_full_name are required'
        }), 400
    
    try:
        result = pat_auth.check_repo_access(pat, repo_full_name)
        
        if result['accessible']:
            return jsonify({
                'success': True,
                'repo_info': result['repo_info']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Access denied')
            }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests', methods=['GET'])
def get_tests():
    """테스트 기록 조회"""
    user_id = request.args.get('user_id', 'default')
    subscription_id = request.args.get('subscription_id', type=int)
    limit = request.args.get('limit', 50, type=int)
    
    db = next(get_db())
    try:
        query = db.query(Test)
        
        if subscription_id:
            query = query.filter(Test.subscription_id == subscription_id)
        else:
            # 사용자의 구독에 해당하는 테스트만
            subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).all()
            subscription_ids = [s.id for s in subscriptions]
            if subscription_ids:
                query = query.filter(Test.subscription_id.in_(subscription_ids))
            else:
                # 구독이 없으면 빈 결과
                return jsonify({
                    'success': True,
                    'tests': []
                }), 200
        
        tests = query.order_by(Test.created_at.desc()).limit(limit).all()
        
        results = []
        for test in tests:
            results.append({
                'id': test.id,
                'subscription_id': test.subscription_id,
                'pr_number': test.pr_number,
                'pr_url': test.pr_url,
                'repo_full_name': test.repo_full_name,
                'status': test.status,
                'test_results': test.test_results,
                'created_at': test.created_at.isoformat() if test.created_at else None,
                'completed_at': test.completed_at.isoformat() if test.completed_at else None
            })
        
        return jsonify({
            'success': True,
            'tests': results
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()

@app.route('/api/tests/<int:test_id>', methods=['GET'])
def get_test(test_id):
    """특정 테스트 결과 조회"""
    db = next(get_db())
    try:
        test = db.query(Test).filter(Test.id == test_id).first()
        
        if test:
            return jsonify({
                'success': True,
                'test': {
                    'id': test.id,
                    'subscription_id': test.subscription_id,
                    'pr_number': test.pr_number,
                    'pr_url': test.pr_url,
                    'repo_full_name': test.repo_full_name,
                    'status': test.status,
                    'test_results': test.test_results,
                    'report_path': test.report_path,
                    'created_at': test.created_at.isoformat() if test.created_at else None,
                    'completed_at': test.completed_at.isoformat() if test.completed_at else None
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Test not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()

if __name__ == '__main__':
    # 데이터베이스 초기화
    init_db()
    
    port = int(os.getenv('API_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)


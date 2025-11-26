# server/controllers/subscription_controller.py
"""
구독 관리 컨트롤러
"""
from flask import request, jsonify
from ..services.subscription_service import SubscriptionService

class SubscriptionController:
    """구독 관리 컨트롤러"""
    
    def __init__(self):
        self.service = SubscriptionService()
    
    def get_subscriptions(self):
        """구독 목록 조회"""
        user_id = request.args.get('user_id', 'default')
        
        try:
            subscriptions = self.service.get_subscriptions(user_id)
            return jsonify({
                'success': True,
                'subscriptions': subscriptions
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def create_subscription(self):
        """레포지토리 구독 생성"""
        data = request.json
        
        user_id = data.get('user_id', 'default')
        repo_full_name = data.get('repo_full_name')
        pat = data.get('pat')  # Optional: Public 저장소는 PAT 불필요
        auto_test = data.get('auto_test', True)
        slack_notify = data.get('slack_notify', True)
        exclude_branches = data.get('exclude_branches')  # 제외할 브랜치 목록
        test_options = data.get('test_options', {})
        
        if not repo_full_name:
            return jsonify({
                'success': False,
                'error': 'repo_full_name is required'
            }), 400
        
        try:
            # 제외할 브랜치 목록 처리 (기본값: ['main'])
            exclude_branches_list = None
            if exclude_branches:
                exclude_branches_list = exclude_branches.split(',') if isinstance(exclude_branches, str) else exclude_branches
                exclude_branches_list = [b.strip() for b in exclude_branches_list if b.strip()]
            
            result = self.service.create_subscription(
                user_id=user_id,
                repo_full_name=repo_full_name,
                pat=pat,
                auto_test=auto_test,
                slack_notify=slack_notify,
                exclude_branches=exclude_branches_list,
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
    
    def get_subscription(self, subscription_id):
        """특정 구독 정보 조회"""
        user_id = request.args.get('user_id', 'default')
        
        try:
            subscriptions = self.service.get_subscriptions(user_id)
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
    
    def delete_subscription(self, subscription_id):
        """구독 삭제"""
        user_id = request.args.get('user_id', 'default')
        
        try:
            success = self.service.delete_subscription(subscription_id, user_id)
            
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


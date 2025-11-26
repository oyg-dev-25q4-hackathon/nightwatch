# server/routes/api_routes.py
"""
API 라우트 정의
"""
from flask import Blueprint, request
from ..controllers.subscription_controller import SubscriptionController
from ..controllers.pat_controller import PATController
from ..controllers.test_controller import TestController

# Blueprint 생성
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 컨트롤러 인스턴스 생성
subscription_controller = SubscriptionController()
pat_controller = PATController()
test_controller = TestController()

# 구독 관련 라우트
@api_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    return subscription_controller.get_subscriptions()

@api_bp.route('/subscriptions', methods=['POST'])
def create_subscription():
    return subscription_controller.create_subscription()

@api_bp.route('/subscriptions/<int:subscription_id>', methods=['GET'])
def get_subscription(subscription_id):
    return subscription_controller.get_subscription(subscription_id)

@api_bp.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
def delete_subscription(subscription_id):
    return subscription_controller.delete_subscription(subscription_id)

@api_bp.route('/subscriptions/<int:subscription_id>/poll', methods=['POST', 'OPTIONS'])
def trigger_polling(subscription_id):
    if request.method == 'OPTIONS':
        return '', 200
    return subscription_controller.trigger_polling(subscription_id)

@api_bp.route('/subscriptions/<int:subscription_id>/pat', methods=['PUT', 'OPTIONS'])
def update_subscription_pat(subscription_id):
    if request.method == 'OPTIONS':
        return '', 200
    return subscription_controller.update_subscription_pat(subscription_id)

@api_bp.route('/subscriptions/poll-all', methods=['POST', 'OPTIONS'])
def trigger_all_polling():
    if request.method == 'OPTIONS':
        return '', 200
    return subscription_controller.trigger_all_polling()

# PAT 관련 라우트
@api_bp.route('/pat/verify', methods=['POST'])
def verify_pat():
    return pat_controller.verify_pat()

@api_bp.route('/pat/check-repo', methods=['POST'])
def check_repo_access():
    return pat_controller.check_repo_access()

# 테스트 관련 라우트
@api_bp.route('/tests', methods=['GET'])
def get_tests():
    return test_controller.get_tests()

@api_bp.route('/tests/<int:test_id>', methods=['GET'])
def get_test(test_id):
    return test_controller.get_test(test_id)

@api_bp.route('/tests/<int:test_id>/rerun-scenario', methods=['POST', 'OPTIONS'])
def rerun_scenario(test_id):
    if request.method == 'OPTIONS':
        return '', 200
    return test_controller.rerun_scenario(test_id)


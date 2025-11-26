# server/controllers/test_controller.py
"""
테스트 기록 컨트롤러
"""
from flask import request, jsonify
from ..models import Test, Subscription, get_db

class TestController:
    """테스트 기록 컨트롤러"""
    
    def get_tests(self):
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
                subscriptions = db.query(Subscription).filter(
                    Subscription.user_id == user_id
                ).all()
                subscription_ids = [s.id for s in subscriptions]
                if subscription_ids:
                    query = query.filter(Test.subscription_id.in_(subscription_ids))
                else:
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
    
    def get_test(self, test_id):
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


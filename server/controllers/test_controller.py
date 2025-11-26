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
    
    def create_dummy_test(self):
        """테스트용 더미 PR 생성"""
        from datetime import datetime
        import random
        
        data = request.json
        subscription_id = data.get('subscription_id')
        pr_number = data.get('pr_number', random.randint(100, 999))
        status = data.get('status', 'completed')  # pending, running, completed, failed
        
        if not subscription_id:
            return jsonify({
                'success': False,
                'error': 'subscription_id is required'
            }), 400
        
        db = next(get_db())
        try:
            # 구독 정보 확인
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'Subscription not found'
                }), 404
            
            # 더미 테스트 결과 생성
            dummy_results = [
                {
                    'description': '메인 페이지 로드 테스트',
                    'actions': [
                        {'type': 'goto', 'url': f'https://pr-{pr_number}.{subscription.repo_full_name.split("/")[1]}.com'},
                        {'type': 'wait', 'seconds': 2},
                        {'type': 'screenshot', 'name': 'main_page'}
                    ],
                    'success': True,
                    'error': None
                },
                {
                    'description': '로그인 버튼 클릭 테스트',
                    'actions': [
                        {'type': 'click', 'selector': 'button.login'},
                        {'type': 'wait', 'seconds': 1},
                        {'type': 'screenshot', 'name': 'login_modal'}
                    ],
                    'success': True,
                    'error': None
                },
                {
                    'description': '검색 기능 테스트',
                    'actions': [
                        {'type': 'fill', 'selector': 'input.search', 'value': 'test query'},
                        {'type': 'click', 'selector': 'button.search-submit'},
                        {'type': 'wait', 'seconds': 2},
                        {'type': 'screenshot', 'name': 'search_results'}
                    ],
                    'success': status != 'failed',
                    'error': 'Failed to find search results' if status == 'failed' else None
                }
            ]
            
            # 테스트 레코드 생성
            test = Test(
                subscription_id=subscription_id,
                pr_number=pr_number,
                pr_url=f'https://github.com/{subscription.repo_full_name}/pull/{pr_number}',
                repo_full_name=subscription.repo_full_name,
                status=status,
                test_results=dummy_results,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if status in ['completed', 'failed'] else None
            )
            
            db.add(test)
            db.commit()
            
            return jsonify({
                'success': True,
                'test': {
                    'id': test.id,
                    'pr_number': test.pr_number,
                    'status': test.status,
                    'created_at': test.created_at.isoformat()
                }
            }), 201
            
        except Exception as e:
            db.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        finally:
            db.close()


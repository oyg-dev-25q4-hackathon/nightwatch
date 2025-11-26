# server/controllers/test_controller.py
"""
테스트 기록 컨트롤러
"""
from flask import request, jsonify
from ..models import Test, Subscription, get_db
from ..services.test_pipeline_service import TestPipelineService
from ..services.pat_auth_service import PATAuthService
from github import Github
import os

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
                    'pr_title': test.pr_title,
                    'pr_url': test.pr_url,
                    'branch_name': test.branch_name,
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
                        'pr_title': test.pr_title,
                        'pr_url': test.pr_url,
                        'branch_name': test.branch_name,
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
    
    def rerun_scenario(self, test_id):
        """특정 시나리오 재실행"""
        data = request.json or {}
        scenario_index = data.get('scenario_index', 0)
        
        db = next(get_db())
        try:
            test = db.query(Test).filter(Test.id == test_id).first()
            
            if not test:
                return jsonify({
                    'success': False,
                    'error': 'Test not found'
                }), 404
            
            # 테스트 결과에서 시나리오 가져오기
            test_results = test.test_results
            if not test_results:
                return jsonify({
                    'success': False,
                    'error': 'No test results found'
                }), 400
            
            # test_results가 문자열인 경우 파싱
            if isinstance(test_results, str):
                import json
                test_results = json.loads(test_results)
            
            # 시나리오 배열 확인
            if not isinstance(test_results, list) or len(test_results) <= scenario_index:
                return jsonify({
                    'success': False,
                    'error': f'Scenario index {scenario_index} not found'
                }), 400
            
            scenario_result = test_results[scenario_index]
            
            # PR 정보 가져오기
            repo_name = test.repo_full_name
            pr_number = test.pr_number
            
            # 구독 정보에서 PAT 가져오기
            subscription = db.query(Subscription).filter(
                Subscription.id == test.subscription_id
            ).first()
            
            pat = None
            pat_auth = PATAuthService()
            if subscription and subscription.user_credential_id:
                credential = pat_auth.get_credential_by_id(subscription.user_credential_id)
                if credential:
                    pat = pat_auth.get_decrypted_pat(credential.user_id)
            
            # GitHub에서 PR 정보 가져오기
            try:
                if pat:
                    g = Github(pat)
                else:
                    # PAT가 없으면 Public 저장소로 접근 시도
                    g = Github()
                
                repo = g.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'GitHub API error: {str(e)}. PAT가 필요할 수 있습니다.'
                }), 401
            
            # PR 배포 URL 생성
            # subscription의 base_url 우선 사용, 없으면 로컬 모드 확인
            if subscription and subscription.base_url:
                base_url = subscription.base_url
                pr_url = f"pr-{pr_number}.{base_url}"
            else:
                # base_url이 없으면 로컬 모드로 실행 (localhost:5173 사용)
                pr_url = "localhost:5173"
                base_url = None  # 로컬 모드에서는 base_url이 필요 없음
            
            # 시나리오 재실행
            pipeline_service = TestPipelineService(base_url=base_url or os.getenv('BASE_URL', 'localhost:5173'))
            
            # 결과 객체에서 원본 시나리오 정보 복원
            # scenario_result가 결과 형태인 경우 원본 형태로 변환
            if 'actions' in scenario_result:
                # 이미 원본 시나리오 형태
                scenario = scenario_result
            else:
                # 결과 형태에서 원본 형태로 복원 시도
                # actions_executed에서 원본 actions 추출 시도
                scenario = {
                    'name': scenario_result.get('scenario_name', f'Scenario {scenario_index + 1}'),
                    'description': scenario_result.get('description', ''),
                    'expected_result': scenario_result.get('expected_result', ''),
                    'actions': []
                }
                
                # actions_executed에서 원본 actions 추출
                actions_executed = scenario_result.get('actions_executed', [])
                for action_result in actions_executed:
                    if 'action' in action_result:
                        scenario['actions'].append(action_result['action'])
                    elif 'type' in action_result:
                        # action_result 자체가 action 형태일 수 있음
                        scenario['actions'].append({
                            'type': action_result.get('type'),
                            **{k: v for k, v in action_result.items() if k not in ['success', 'error', 'screenshot']}
                        })
                
                # actions가 비어있으면 PR diff를 다시 분석하여 시나리오 재생성
                if not scenario['actions']:
                    pr_diff = pipeline_service.get_pr_diff(pr)
                    from ..services.pr_analyzer_service import PRAnalyzerService
                    analyzer = PRAnalyzerService(base_url=base_url)
                    all_scenarios = analyzer.analyze_and_generate_scenarios(pr_diff, pr_url=pr_url)
                    
                    # 해당 인덱스의 시나리오 찾기 (이름으로 매칭)
                    scenario_name = scenario_result.get('scenario_name', '')
                    matching_scenario = None
                    for s in all_scenarios:
                        if s.get('name') == scenario_name or s.get('description') == scenario_result.get('description', ''):
                            matching_scenario = s
                            break
                    
                    if matching_scenario:
                        scenario = matching_scenario
                    elif scenario_index < len(all_scenarios):
                        # 이름 매칭 실패 시 인덱스로 매칭
                        scenario = all_scenarios[scenario_index]
                    else:
                        return jsonify({
                            'success': False,
                            'error': '원본 시나리오를 복원할 수 없습니다.'
                        }), 400
            
            result = pipeline_service.rerun_scenario(scenario, pr_url=pr_url)
            
            # 테스트 결과 업데이트
            test_results[scenario_index] = result
            
            # DB 업데이트
            test.test_results = test_results
            db.commit()
            
            return jsonify({
                'success': True,
                'result': result,
                'message': f'Scenario {scenario_index + 1} rerun completed'
            }), 200
            
        except Exception as e:
            db.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        finally:
            db.close()
    
    def regenerate_scenarios(self, test_id):
        """시나리오 재생성 (실행 없이 시나리오만 생성)"""
        db = next(get_db())
        try:
            test = db.query(Test).filter(Test.id == test_id).first()
            
            if not test:
                return jsonify({
                    'success': False,
                    'error': 'Test not found'
                }), 404
            
            # 구독 정보 가져오기
            subscription = db.query(Subscription).filter(
                Subscription.id == test.subscription_id
            ).first()
            
            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'Subscription not found'
                }), 404
            
            # PAT 가져오기
            pat = None
            pat_auth = PATAuthService()
            if subscription.user_credential_id:
                credential = pat_auth.get_credential_by_id(subscription.user_credential_id)
                if credential:
                    pat = pat_auth.get_decrypted_pat(credential.user_id)
            
            # GitHub에서 PR 정보 가져오기
            try:
                if pat:
                    g = Github(pat)
                else:
                    g = Github()
                
                repo = g.get_repo(test.repo_full_name)
                pr = repo.get_pull(test.pr_number)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'GitHub API error: {str(e)}. PAT가 필요할 수 있습니다.'
                }), 401
            
            # PR diff 가져오기
            pipeline_service = TestPipelineService(base_url=subscription.base_url)
            pr_diff = pipeline_service.get_pr_diff(pr)
            
            # PR 배포 URL 생성
            if subscription.base_url:
                base_url = subscription.base_url
                pr_url = f"pr-{test.pr_number}.{base_url}"
            else:
                # base_url이 없으면 로컬 모드로 실행 (localhost:5173 사용)
                pr_url = "localhost:5173"
                base_url = None
            
            # 시나리오 재생성
            from ..services.pr_analyzer_service import PRAnalyzerService
            analyzer = PRAnalyzerService(base_url=base_url)
            try:
                scenarios = analyzer.analyze_and_generate_scenarios(pr_diff, pr_url=pr_url)
            except ValueError as e:
                # API 키 관련 에러 등 명시적인 에러
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            except Exception as e:
                # 기타 예상치 못한 에러
                return jsonify({
                    'success': False,
                    'error': f'시나리오 생성 중 오류가 발생했습니다: {str(e)}'
                }), 500
            
            # test_results를 시나리오만 저장 (실행 결과 없음)
            # 시나리오를 원본 형태로 저장
            test.test_results = scenarios
            test.status = 'pending'  # 시나리오만 생성되었으므로 pending 상태
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'{len(scenarios)}개의 시나리오가 생성되었습니다.',
                'scenarios_count': len(scenarios),
                'scenarios': scenarios
            }), 200
            
        except Exception as e:
            db.rollback()
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error regenerating scenarios: {str(e)}\n{error_trace}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()


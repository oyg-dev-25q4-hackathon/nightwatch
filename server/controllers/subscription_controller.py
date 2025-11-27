# server/controllers/subscription_controller.py
"""
구독 관리 컨트롤러
"""
from flask import request, jsonify
from ..services.subscription_service import SubscriptionService
from ..services.polling_service import PollingService
from ..models import Subscription, get_db

class SubscriptionController:
    """구독 관리 컨트롤러"""
    
    def __init__(self):
        self.service = SubscriptionService()
        self.polling_service = PollingService()
    
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
        pat = data.get('pat')  # 필수
        auto_test = data.get('auto_test', True)
        slack_notify = data.get('slack_notify', True)
        exclude_branches = data.get('exclude_branches')  # 제외할 브랜치 목록
        test_options = data.get('test_options', {})
        # preview 브랜치만 테스트 대상이므로 base_url은 사용하지 않음 (항상 preview-dev.oliveyoung.com 사용)
        
        if not repo_full_name:
            return jsonify({
                'success': False,
                'error': 'repo_full_name is required'
            }), 400
        
        if not pat or not pat.strip():
            return jsonify({
                'success': False,
                'error': 'pat (Personal Access Token) is required'
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
                test_options=test_options,
                base_url=None  # base_url은 사용하지 않음
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
        """특정 구독 정보 조회 (모든 PR 목록 포함)"""
        user_id = request.args.get('user_id', 'default')
        
        db = next(get_db())
        try:
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).first()
            
            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'Subscription not found'
                }), 404
            
            subscription_dict = self.service._subscription_to_dict(subscription)
            
            # GitHub에서 모든 PR 목록 가져오기 (테스트 대상/미대상 분리)
            all_prs = []
            non_target_prs = []
            
            try:
                # PAT 가져오기
                pat = None
                if subscription.user_credential_id:
                    credential = self.polling_service.pat_auth.get_credential_by_id(subscription.user_credential_id)
                    if credential:
                        pat = self.polling_service.pat_auth.get_decrypted_pat(credential.user_id)
                
                # GitHub API로 PR 목록 가져오기
                from github import Github
                if pat:
                    g = Github(pat)
                else:
                    g = Github()
                
                repo = g.get_repo(subscription.repo_full_name)
                pulls = repo.get_pulls(state='open', sort='updated', direction='desc')
                
                for pr in pulls:
                    pr_info = {
                        'number': pr.number,
                        'title': pr.title,
                        'branch': pr.head.ref,
                        'url': pr.html_url,
                        'created_at': pr.created_at.isoformat() if pr.created_at else None,
                        'updated_at': pr.updated_at.isoformat() if pr.updated_at else None,
                    }
                    
                    # 테스트 대상 확인: 정확히 "preview" 브랜치
                    if pr.head.ref == "preview":
                        all_prs.append(pr_info)
                    else:
                        # 제외 브랜치가 아닌 경우만 미대상 목록에 추가
                        exclude_branches = subscription.exclude_branches or ['main']
                        should_exclude = False
                        for exclude_branch in exclude_branches:
                            if exclude_branch.endswith('*'):
                                pattern = exclude_branch.replace('*', '')
                                if pr.head.ref.startswith(pattern):
                                    should_exclude = True
                                    break
                            elif pr.head.ref == exclude_branch:
                                should_exclude = True
                                break
                        
                        if not should_exclude:
                            non_target_prs.append(pr_info)
            except Exception as e:
                print(f"⚠️ Failed to fetch PRs from GitHub: {e}")
                # 에러가 발생해도 구독 정보는 반환
            
            return jsonify({
                'success': True,
                'subscription': subscription_dict,
                'target_prs': all_prs,  # 테스트 대상 PR (preview 브랜치)
                'non_target_prs': non_target_prs  # 테스트 미대상 PR
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        finally:
            db.close()
    
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
    
    def trigger_polling(self, subscription_id):
        """특정 구독에 대해 즉시 PR 감지 실행"""
        user_id = request.args.get('user_id', 'default')
        
        db = next(get_db())
        try:
            # 구독 정보 확인
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).first()
            
            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'Subscription not found or inactive'
                }), 404
            
            # 즉시 polling 실행
            try:
                detected_count, detected_pr_list, non_target_pr_list = self.polling_service._poll_subscription(subscription)
                return jsonify({
                    'success': True,
                    'message': f'Polling completed for {subscription.repo_full_name}',
                    'detected_prs': detected_count,
                    'pr_list': detected_pr_list,  # 테스트 대상 PR (preview 브랜치)
                    'non_target_pr_list': non_target_pr_list  # 테스트 미대상 PR
                }), 200
            except Exception as e:
                error_msg = str(e)
                # Rate limit 에러인 경우 특별 처리
                if 'rate limit' in error_msg.lower():
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'error_type': 'rate_limit',
                        'suggestion': 'Please add a Personal Access Token (PAT) to increase the rate limit from 60/hour to 5,000/hour'
                    }), 429  # Too Many Requests
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Polling failed: {error_msg}'
                    }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        finally:
            db.close()
    
    def trigger_all_polling(self):
        """모든 활성 구독에 대해 즉시 PR 감지 실행"""
        try:
            self.polling_service.poll_all_subscriptions()
            return jsonify({
                'success': True,
                'message': 'Polling completed for all active subscriptions'
            }), 200
        except Exception as e:
            error_msg = str(e)
            # Rate limit 에러인 경우 특별 처리
            if 'rate limit' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'error_type': 'rate_limit',
                    'suggestion': 'Please add a Personal Access Token (PAT) to increase the rate limit from 60/hour to 5,000/hour'
                }), 429  # Too Many Requests
            else:
                return jsonify({
                    'success': False,
                    'error': f'Polling failed: {error_msg}'
                }), 500
    
    def update_subscription_pat(self, subscription_id):
        """기존 구독에 PAT 추가/업데이트"""
        data = request.json
        user_id = data.get('user_id', request.args.get('user_id', 'default'))
        pat = data.get('pat')
        
        if not pat:
            return jsonify({
                'success': False,
                'error': 'pat is required'
            }), 400
        
        try:
            result = self.service.update_subscription_pat(subscription_id, user_id, pat)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message']
                }), 200
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


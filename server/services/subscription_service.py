# server/services/subscription_service.py
"""
레포지토리 구독 관리 서비스
"""
from typing import List, Dict
from datetime import datetime
from ..models import Subscription, get_db
from .pat_auth_service import PATAuthService

class SubscriptionService:
    """구독 관리 서비스"""
    
    def __init__(self):
        self.pat_auth = PATAuthService()
    
    def create_subscription(
        self,
        user_id: str,
        repo_full_name: str,
        pat: str = None,
        auto_test: bool = True,
        slack_notify: bool = True,
        exclude_branches: List[str] = None,
        test_options: Dict = None
    ) -> Dict:
        """레포지토리 구독 생성"""
        credential_id = None
        
        # 레포지토리 이름 정규화 (URL 형식 지원)
        normalized_repo = self._normalize_repo_name(repo_full_name)
        if not normalized_repo or '/' not in normalized_repo:
            return {
                'success': False,
                'error': 'Invalid repository format. Use owner/repo-name or GitHub URL'
            }
        repo_full_name = normalized_repo  # 정규화된 이름 사용
        
        # PAT가 제공된 경우: 검증 및 저장
        if pat:
            # 1. PAT 검증
            verify_result = self.pat_auth.verify_pat(pat)
            if not verify_result['valid']:
                return {
                    'success': False,
                    'error': f"PAT verification failed: {verify_result.get('error')}"
                }
            
            # 2. 레포지토리 접근 권한 확인
            access_result = self.pat_auth.check_repo_access(pat, repo_full_name)
            if not access_result['accessible']:
                return {
                    'success': False,
                    'error': f"Repository access denied: {access_result.get('error')}"
                }
            
            # 3. 인증 정보 저장
            try:
                credential_id = self.pat_auth.save_credential(
                    user_id=user_id,
                    pat=pat,
                    github_username=verify_result['username'],
                    token_scopes=None
                )
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to save credential: {str(e)}"
                }
        else:
            # PAT가 없는 경우: Public 저장소인지 확인
            public_check = self.pat_auth.check_repo_public(repo_full_name)
            if not public_check['exists']:
                return {
                    'success': False,
                    'error': f"Repository not found: {public_check.get('error')}"
                }
            
            if not public_check['is_public']:
                return {
                    'success': False,
                    'error': 'Private repository requires PAT. Please provide a Personal Access Token.'
                }
            
            print(f"  ℹ️ Public repository detected: {repo_full_name}")
        
        # 4. 구독 정보 저장
        db = next(get_db())
        try:
            existing = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.repo_full_name == repo_full_name,
                Subscription.is_active == True
            ).first()
            
            if existing:
                existing.auto_test = auto_test
                existing.slack_notify = slack_notify
                # 기본값: main만 제외
                existing.exclude_branches = exclude_branches if exclude_branches is not None else ['main']
                existing.test_options = test_options or {}
                existing.user_credential_id = credential_id
                existing.updated_at = datetime.utcnow()
                subscription_id = existing.id
            else:
                repo_parts = repo_full_name.split('/')
                if len(repo_parts) != 2:
                    return {
                        'success': False,
                        'error': 'Invalid repository format. Use owner/repo-name'
                    }
                
                subscription = Subscription(
                    user_id=user_id,
                    user_credential_id=credential_id,
                    repo_owner=repo_parts[0],
                    repo_name=repo_parts[1],
                    repo_full_name=repo_full_name,
                    auto_test=auto_test,
                    slack_notify=slack_notify,
                    # 기본값: main만 제외
                    exclude_branches=exclude_branches if exclude_branches is not None else ['main'],
                    test_options=test_options or {},
                    is_active=True,
                    last_polled_at=datetime.utcnow()
                )
                db.add(subscription)
                subscription_id = subscription.id
            
            db.commit()
            return {
                'success': True,
                'subscription_id': subscription_id
            }
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'error': f"Failed to create subscription: {str(e)}"
            }
        finally:
            db.close()
    
    def get_subscriptions(self, user_id: str) -> List[Dict]:
        """사용자의 구독 목록 조회"""
        db = next(get_db())
        try:
            subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).all()
            
            return [self._subscription_to_dict(sub) for sub in subscriptions]
        finally:
            db.close()
    
    def get_all_active_subscriptions(self) -> List[Subscription]:
        """모든 활성 구독 조회 (Polling용)"""
        db = next(get_db())
        try:
            return db.query(Subscription).filter(
                Subscription.is_active == True,
                Subscription.auto_test == True
            ).all()
        finally:
            db.close()
    
    def delete_subscription(self, subscription_id: int, user_id: str) -> bool:
        """구독 삭제 (비활성화)"""
        db = next(get_db())
        try:
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id
            ).first()
            
            if subscription:
                subscription.is_active = False
                subscription.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def update_last_polled(self, subscription_id: int):
        """마지막 Polling 시간 업데이트"""
        db = next(get_db())
        try:
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if subscription:
                subscription.last_polled_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
    
    def _normalize_repo_name(self, repo_input: str) -> str:
        """GitHub URL을 owner/repo 형식으로 변환"""
        if not repo_input:
            return ''
        
        import re
        normalized = repo_input.strip()
        
        # 앞뒤 슬래시 제거
        normalized = re.sub(r'^/+|/+$', '', normalized)
        
        # https://github.com/owner/repo 형식인 경우
        github_url_pattern = r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.search(github_url_pattern, normalized)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        
        # 이미 owner/repo 형식인 경우 (앞뒤 슬래시 제거 후)
        if '/' in normalized and 'http' not in normalized:
            return normalized
        
        return normalized
    
    def _subscription_to_dict(self, subscription: Subscription) -> Dict:
        """Subscription 객체를 딕셔너리로 변환"""
        return {
            'id': subscription.id,
            'repo_full_name': subscription.repo_full_name,
            'repo_owner': subscription.repo_owner,
            'repo_name': subscription.repo_name,
            'auto_test': subscription.auto_test,
            'slack_notify': subscription.slack_notify,
            'exclude_branches': subscription.exclude_branches,
            'test_options': subscription.test_options,
            'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
            'last_polled_at': subscription.last_polled_at.isoformat() if subscription.last_polled_at else None
        }


# src/subscription_manager.py
"""
레포지토리 구독 관리 모듈
"""
from typing import List, Dict, Optional
from datetime import datetime
from .models import Subscription, get_db
from .pat_auth import PATAuth

class SubscriptionManager:
    """구독 관리 클래스"""
    
    def __init__(self):
        self.pat_auth = PATAuth()
    
    def create_subscription(
        self,
        user_id: str,
        repo_full_name: str,
        pat: str,
        auto_test: bool = True,
        slack_notify: bool = True,
        target_branches: List[str] = None,
        test_options: Dict = None
    ) -> Dict:
        """
        레포지토리 구독 생성
        
        Args:
            user_id: 사용자 식별자
            repo_full_name: owner/repo 형식
            pat: Personal Access Token
            auto_test: 자동 테스트 실행 여부
            slack_notify: Slack 알림 여부
            target_branches: 특정 브랜치만 (None이면 모든 브랜치)
            test_options: 테스트 옵션
            
        Returns:
            {
                'success': bool,
                'subscription_id': int (if success),
                'error': str (if failed)
            }
        """
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
                token_scopes=None  # 필요시 추가
            )
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to save credential: {str(e)}"
            }
        
        # 4. 구독 정보 저장
        db = next(get_db())
        try:
            # 기존 구독 확인
            existing = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.repo_full_name == repo_full_name,
                Subscription.is_active == True
            ).first()
            
            if existing:
                # 기존 구독 업데이트
                existing.auto_test = auto_test
                existing.slack_notify = slack_notify
                existing.target_branches = target_branches
                existing.test_options = test_options or {}
                existing.user_credential_id = credential_id
                existing.updated_at = datetime.utcnow()
                subscription_id = existing.id
            else:
                # 새 구독 생성
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
                    target_branches=target_branches,
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
    
    def _subscription_to_dict(self, subscription: Subscription) -> Dict:
        """Subscription 객체를 딕셔너리로 변환"""
        return {
            'id': subscription.id,
            'repo_full_name': subscription.repo_full_name,
            'repo_owner': subscription.repo_owner,
            'repo_name': subscription.repo_name,
            'auto_test': subscription.auto_test,
            'slack_notify': subscription.slack_notify,
            'target_branches': subscription.target_branches,
            'test_options': subscription.test_options,
            'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
            'last_polled_at': subscription.last_polled_at.isoformat() if subscription.last_polled_at else None
        }


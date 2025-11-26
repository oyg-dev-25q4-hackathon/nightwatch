# server/services/pat_auth_service.py
"""
Personal Access Token 인증 서비스
"""
import requests
from typing import Dict, Optional
from datetime import datetime
from ..models import UserCredential, get_db
from ..utils.crypto import encrypt_pat, decrypt_pat

class PATAuthService:
    """PAT 인증 및 관리 서비스"""
    
    def __init__(self):
        self.github_base_url = "https://api.github.com"
    
    def verify_pat(self, pat: str) -> Dict:
        """PAT 유효성 검증"""
        try:
            headers = {
                'Authorization': f'token {pat}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                f'{self.github_base_url}/user',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    'valid': True,
                    'username': user_info.get('login'),
                    'user_id': str(user_info.get('id')),
                    'repos_url': user_info.get('repos_url')
                }
            elif response.status_code == 401:
                return {
                    'valid': False,
                    'error': 'Invalid or expired token'
                }
            else:
                return {
                    'valid': False,
                    'error': f'GitHub API error: {response.status_code}'
                }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def check_repo_access(self, pat: str, repo_full_name: str) -> Dict:
        """레포지토리 접근 권한 확인"""
        try:
            headers = {
                'Authorization': f'token {pat}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                f'{self.github_base_url}/repos/{repo_full_name}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                repo_info = response.json()
                return {
                    'accessible': True,
                    'repo_info': repo_info,
                    'is_public': not repo_info.get('private', True)
                }
            elif response.status_code == 404:
                return {
                    'accessible': False,
                    'error': 'Repository not found or no access permission'
                }
            else:
                return {
                    'accessible': False,
                    'error': f'GitHub API error: {response.status_code}'
                }
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e)
            }
    
    def check_repo_public(self, repo_full_name: str) -> Dict:
        """Public 저장소인지 확인 (PAT 없이)"""
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                f'{self.github_base_url}/repos/{repo_full_name}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                repo_info = response.json()
                is_public = not repo_info.get('private', True)
                return {
                    'exists': True,
                    'is_public': is_public,
                    'repo_info': repo_info if is_public else None
                }
            elif response.status_code == 404:
                return {
                    'exists': False,
                    'is_public': False,
                    'error': 'Repository not found'
                }
            else:
                return {
                    'exists': False,
                    'is_public': False,
                    'error': f'GitHub API error: {response.status_code}'
                }
        except Exception as e:
            return {
                'exists': False,
                'is_public': False,
                'error': str(e)
            }
    
    def save_credential(self, user_id: str, pat: str, github_username: str, token_scopes: list = None) -> int:
        """인증 정보를 암호화하여 저장"""
        db = next(get_db())
        try:
            existing = db.query(UserCredential).filter(
                UserCredential.user_id == user_id
            ).first()
            
            encrypted_pat = encrypt_pat(pat)
            
            if existing:
                existing.encrypted_pat = encrypted_pat
                existing.github_username = github_username
                existing.token_scopes = token_scopes
                existing.last_verified_at = datetime.utcnow()
                credential_id = existing.id
            else:
                credential = UserCredential(
                    user_id=user_id,
                    github_username=github_username,
                    encrypted_pat=encrypted_pat,
                    token_scopes=token_scopes,
                    last_verified_at=datetime.utcnow()
                )
                db.add(credential)
                credential_id = credential.id
            
            db.commit()
            return credential_id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_decrypted_pat(self, user_id: str) -> Optional[str]:
        """사용자의 암호화된 PAT를 복호화하여 반환"""
        db = next(get_db())
        try:
            credential = db.query(UserCredential).filter(
                UserCredential.user_id == user_id
            ).first()
            
            if credential:
                return decrypt_pat(credential.encrypted_pat)
            return None
        finally:
            db.close()
    
    def get_credential_by_id(self, credential_id: int) -> Optional[UserCredential]:
        """인증 정보 ID로 조회"""
        db = next(get_db())
        try:
            return db.query(UserCredential).filter(
                UserCredential.id == credential_id
            ).first()
        finally:
            db.close()


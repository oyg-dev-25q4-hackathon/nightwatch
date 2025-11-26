# src/pat_auth.py
"""
Personal Access Token 인증 모듈
"""
import requests
from github import Github
from typing import Dict, Optional
from .crypto_utils import encrypt_pat, decrypt_pat
from .models import UserCredential, get_db

class PATAuth:
    """PAT 인증 및 관리 클래스"""
    
    def __init__(self):
        self.github_base_url = "https://api.github.com"
    
    def verify_pat(self, pat: str) -> Dict:
        """
        PAT 유효성 검증
        
        Args:
            pat: Personal Access Token
            
        Returns:
            {
                'valid': bool,
                'username': str (if valid),
                'error': str (if invalid)
            }
        """
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
        """
        레포지토리 접근 권한 확인
        
        Args:
            pat: Personal Access Token
            repo_full_name: owner/repo 형식의 레포지토리 이름
            
        Returns:
            {
                'accessible': bool,
                'repo_info': dict (if accessible),
                'error': str (if not accessible)
            }
        """
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
                    'repo_info': repo_info
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
    
    def save_credential(self, user_id: str, pat: str, github_username: str, token_scopes: list = None) -> int:
        """
        인증 정보를 암호화하여 저장
        
        Args:
            user_id: 사용자 식별자
            pat: Personal Access Token
            github_username: GitHub 사용자명
            token_scopes: 토큰 권한 목록
            
        Returns:
            credential_id
        """
        db = next(get_db())
        try:
            # 기존 인증 정보가 있으면 업데이트
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
        """
        사용자의 암호화된 PAT를 복호화하여 반환
        
        Args:
            user_id: 사용자 식별자
            
        Returns:
            복호화된 PAT 또는 None
        """
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

from datetime import datetime
from .models import get_db


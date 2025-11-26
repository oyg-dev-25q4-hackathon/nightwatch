# src/crypto_utils.py
"""
PAT 암호화/복호화 유틸리티
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key():
    """
    환경 변수에서 암호화 키 가져오기 또는 생성
    """
    key = os.getenv('ENCRYPTION_KEY')
    
    if not key:
        # 키가 없으면 새로 생성 (개발 환경용)
        # 프로덕션에서는 반드시 환경 변수로 설정해야 함
        print("⚠️ WARNING: ENCRYPTION_KEY not set. Generating new key for development.")
        key = Fernet.generate_key().decode()
        print(f"Generated key (save this to .env): {key}")
        return key.encode()
    
    # 키가 base64 문자열인 경우
    if isinstance(key, str):
        try:
            # 이미 Fernet 키 형식인지 확인
            Fernet(key.encode())
            return key.encode()
        except:
            # base64로 인코딩된 키를 디코딩
            return base64.b64decode(key)
    
    return key

def encrypt_pat(pat: str) -> str:
    """
    PAT를 암호화하여 반환
    
    Args:
        pat: 암호화할 Personal Access Token
        
    Returns:
        암호화된 PAT (base64 문자열)
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(pat.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_pat(encrypted_pat: str) -> str:
    """
    암호화된 PAT를 복호화하여 반환
    
    Args:
        encrypted_pat: 암호화된 PAT (base64 문자열)
        
    Returns:
        복호화된 PAT
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_pat.encode())
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode()


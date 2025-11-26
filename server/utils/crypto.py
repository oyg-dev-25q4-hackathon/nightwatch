# server/utils/crypto.py
"""
PAT 암호화/복호화 유틸리티
"""
import os
import base64
import binascii
from cryptography.fernet import Fernet

def get_encryption_key():
    """
    환경 변수에서 암호화 키 가져오기 또는 생성
    """
    key = os.getenv('ENCRYPTION_KEY')
    
    if not key:
        print("⚠️ WARNING: ENCRYPTION_KEY not set. Generating new key for development.")
        key = Fernet.generate_key().decode()
        print(f"Generated key (save this to .env): {key}")
        return key.encode()
    
    if isinstance(key, str):
        try:
            Fernet(key.encode())
            return key.encode()
        except:
            return base64.b64decode(key)
    
    return key

def encrypt_pat(pat: str) -> str:
    """PAT를 암호화하여 반환"""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(pat.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_pat(encrypted_pat: str) -> str:
    """암호화된 PAT를 복호화하여 반환"""
    key = get_encryption_key()
    f = Fernet(key)
    try:
        encrypted_bytes = base64.b64decode(encrypted_pat.encode())
    except (binascii.Error, ValueError) as e:
        raise ValueError("Invalid encrypted PAT format") from e
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode()


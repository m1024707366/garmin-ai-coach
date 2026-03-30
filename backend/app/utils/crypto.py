from __future__ import annotations

import base64
from typing import Optional

from cryptography.fernet import Fernet

from src.core.config import settings


def _normalize_key(raw_key: Optional[str]) -> Optional[bytes]:
    if raw_key is None:
        return None

    key = raw_key.strip().encode("utf-8")
    try:
        decoded = base64.urlsafe_b64decode(key)
        if len(decoded) == 32:
            return base64.urlsafe_b64encode(decoded)
    except Exception:
        decoded = None

    if len(key) == 32:
        return base64.urlsafe_b64encode(key)

    return None


def _get_fernet() -> Optional[Fernet]:
    key = _normalize_key(settings.GARMIN_CRED_ENCRYPTION_KEY)
    if key is None:
        return None
    return Fernet(key)


def encrypt_text(plain: str) -> str:
    if plain is None:
        raise ValueError("plain text is required")
    
    fernet = _get_fernet()
    if fernet is None:
        # 没有加密密钥，直接返回明文
        return plain
    
    token = fernet.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(cipher: str) -> str:
    if cipher is None:
        raise ValueError("cipher text is required")
    
    fernet = _get_fernet()
    if fernet is None:
        # 没有加密密钥，直接返回密文（实际是明文）
        return cipher
    
    plain = fernet.decrypt(cipher.encode("utf-8"))
    return plain.decode("utf-8")

"""Token encryption security module using cryptography Fernet.
"""

import os
from cryptography.fernet import Fernet

KEY_FILE = "data/.key"

def _get_or_create_key() -> bytes:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "rb") as f:
                key = f.read()
                if key:
                    return key
        except Exception:
            pass
    key = Fernet.generate_key()
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    except Exception:
        pass
    return key

_fernet = Fernet(_get_or_create_key())

def encrypt_token(token: str) -> str:
    if not token:
        return ""
    return _fernet.encrypt(token.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    try:
        return _fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except Exception:
        return encrypted_token

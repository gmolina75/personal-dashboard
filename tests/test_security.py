import pytest
from app.core.security import encrypt_token, decrypt_token


def test_token_encryption():
    secret = "ya29.a0AfH6SM..."
    encrypted = encrypt_token(secret)
    assert encrypted != secret
    decrypted = decrypt_token(encrypted)
    assert decrypted == secret
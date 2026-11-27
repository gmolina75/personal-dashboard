"""Token encryption security module using Windows DPAPI with Fernet fallback.

- Windows: Uses CryptProtectData / CryptUnprotectData (token binds to user/machine)
- Other OS: Falls back to Fernet with local key file
"""

import os
import sys
import ctypes
import ctypes.wintypes
from typing import Optional

# Try DPAPI for Windows
if sys.platform == "win32":
    class DPAPIError(Exception):
        pass

    class DataProtection:
        """Windows DPAPI wrapper using ctypes."""
        CRYPTPROTECT_UI_FORBIDDEN = 0x1
        CRYPTPROTECT_LOCAL_MACHINE = 0x4

        @staticmethod
        def _make_blob(data: bytes) -> "DATA_BLOB":
            """Create a DATA_BLOB structure from bytes."""
            blob = DATA_BLOB()
            blob.cbData = len(data)
            blob.pbData = (ctypes.c_ubyte * len(data))(*data)
            return blob

        @classmethod
        def protect_bytes(cls, data: bytes, entropy: bytes = None) -> bytes:
            """Encrypt data using CryptProtectData."""
            in_blob = cls._make_blob(data)
            out_blob = DATA_BLOB()

            entropy_blob = cls._make_blob(entropy) if entropy else None

            result = ctypes.windll.crypt32.CryptProtectData(
                ctypes.byref(in_blob),
                None,  # szDataDescr
                entropy_blob,
                None,  # pvOptional = None
                None,  # pvPromptStruct = None  
                cls.CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(out_blob)
            )

            if not result:
                raise DPAPIError(f"CryptProtectData failed: {ctypes.GetLastError()}")

            # Extract encrypted data
            encrypted = bytes((out_blob.pbData[i] for i in range(out_blob.cbData)))

            # Free the output blob
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

            return encrypted

        @classmethod
        def unprotect_bytes(cls, data: bytes, entropy: bytes = None) -> bytes:
            """Decrypt data using CryptUnprotectData."""
            in_blob = cls._make_blob(data)
            out_blob = DATA_BLOB()

            entropy_blob = cls._make_blob(entropy) if entropy else None

            result = ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(in_blob),
                None,  # ppszDataDescr
                entropy_blob,
                None,  # pvOptional
                None,  # pvPromptStruct
                0,  # dwFlags
                ctypes.byref(out_blob)
            )

            if not result:
                error = ctypes.GetLastError()
                if error == 1789:  # NTE_BAD_DATA - data not encrypted for this user
                    # Fallback to Fernet
                    raise ValueError("DPAPI_DECRYPT_FAILED")
                raise DPAPIError(f"CryptUnprotectData failed: {error}")

            decrypted = bytes((out_blob.pbData[i] for i in range(out_blob.cbData)))
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

            return decrypted

else:
    DPAPIError = Exception
    DataProtection = None


# Required Windows structures
if sys.platform == "win32":
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
else:
    # Placeholder for non-Windows
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


# Fernet fallback for non-Windows
from cryptography.fernet import Fernet

KEY_FILE = "data/.key"


def _get_or_create_key() -> bytes:
    """Get or create encryption key for Fernet fallback."""
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
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


# Initialize encryption backend
if sys.platform == "win32" and ctypes.windll:
    _use_dpapi = True
    _fernet = None
else:
    _use_dpapi = False
    _fernet = Fernet(_get_or_create_key())


def encrypt_token(token: str) -> str:
    """Encrypt a token.

    On Windows: Uses DPAPI -> token is bound to user/machine and cannot be moved.
    On other OS: Uses Fernet with local key file.
    """
    if not token:
        return ""

    token_bytes = token.encode("utf-8")

    if _use_dpapi and DataProtection:
        try:
            encrypted = DataProtection.protect_bytes(token_bytes)
            # Prepend version marker for decryption
            return "dpapi_v1:" + encrypted.hex()
        except Exception:
            # Fallback to Fernet if DPAPI fails for any reason
            if _fernet:
                return _fernet.encrypt(token_bytes).decode("utf-8")
            raise

    if _fernet:
        return _fernet.encrypt(token_bytes).decode("utf-8")

    # Last resort - should not happen
    raise RuntimeError("No encryption backend available")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token.

    Windows DPAPI tokens return invalid_grant if moved to another machine.
    Fernet tokens can be decrypted as long as the key file exists.
    """
    if not encrypted_token:
        return ""

    # Handle DPAPI format
    if encrypted_token.startswith("dpapi_v1:"):
        if not _use_dpapi or not DataProtection:
            raise ValueError("Cannot decrypt DPAPI token on non-Windows platform")
        try:
            encrypted_hex = encrypted_token[9:]  # Remove "dpapi_v1:" prefix
            encrypted_bytes = bytes.fromhex(encrypted_hex)
            decrypted = DataProtection.unprotect_bytes(encrypted_bytes)
            return decrypted.decode("utf-8")
        except ValueError as e:
            if str(e) == "DPAPI_DECRYPT_FAILED":
                raise ValueError("Cannot decrypt DPAPI token - token not valid for this user/machine")
            raise
        except Exception as e:
            raise DPAPIError(f"DPAPI decryption failed: {e}")

    try:
        if _fernet:
            return _fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except Exception:
        pass

    return encrypted_token


def is_dpapi_token(token: str) -> bool:
    """Check if a token is DPAPI-encrypted."""
    return token.startswith("dpapi_v1:")
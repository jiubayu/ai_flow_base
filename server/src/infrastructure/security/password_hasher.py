from __future__ import annotations

import hashlib
import hmac
import secrets

SCRYPT_VERSION = "scrypt"
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1


class ScryptPasswordHasher:
    def hash(self, password: str) -> tuple[str, str]:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
        return f"{SCRYPT_VERSION}${salt.hex()}${digest.hex()}", SCRYPT_VERSION

    def verify(self, password: str, stored_digest: str) -> bool:
        try:
            version, salt_hex, digest_hex = stored_digest.split("$", 2)
        except ValueError:
            return False
        if version != SCRYPT_VERSION:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        candidate = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
        return hmac.compare_digest(candidate, expected)

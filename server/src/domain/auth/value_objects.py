from __future__ import annotations

import re
from enum import Enum


class ChallengeState(Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    REPLACED = "replaced"
    ATTEMPTS_EXHAUSTED = "attempts_exhausted"


class SessionState(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REPLACED = "replaced"


class GrantState(Enum):
    ACTIVE = "active"
    ROTATED = "rotated"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AuditEventType(Enum):
    CODE_SENT = "code_sent"
    CODE_RATE_LIMITED = "code_rate_limited"
    REGISTER_SUCCEEDED = "register_succeeded"
    REGISTER_FAILED = "register_failed"
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"
    REFRESH_SUCCEEDED = "refresh_succeeded"
    REFRESH_FAILED = "refresh_failed"
    LOGOUT_SUCCEEDED = "logout_succeeded"
    LOGOUT_FAILED = "logout_failed"


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CODE_PATTERN = re.compile(r"^[0-9]{6}$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(email))


def is_valid_code(code: str) -> bool:
    return bool(CODE_PATTERN.fullmatch(code))


def check_password_policy(password: str) -> str | None:
    """返回 None 表示满足规则；否则返回可读失败原因。"""
    if len(password) < 8:
        return "密码至少需要 8 位"
    if not any(char.isalpha() for char in password):
        return "密码必须包含字母"
    if not any(char.isdigit() for char in password):
        return "密码必须包含数字"
    return None

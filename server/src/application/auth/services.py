from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Protocol


class EmailSender(Protocol):
    def send(self, to: str, code: str, expires_in_seconds: int) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> tuple[str, str]:
        """返回 (digest, version)。"""
        ...

    def verify(self, password: str, stored_digest: str) -> bool: ...


class SessionCookieManager(Protocol):
    def issue(self, session_id: str, grant_id: str, access_max_age: int, refresh_max_age: int) -> tuple[str, str]:
        """返回两条 Set-Cookie 头值（access 与 refresh）。"""
        ...

    def clear(self) -> tuple[str, str]: ...

    def read(self, cookies: Mapping[str, str]) -> tuple[str | None, str | None]: ...


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

from __future__ import annotations

from typing import Mapping

ACCESS_COOKIE_NAME = "access_session"
REFRESH_COOKIE_NAME = "refresh_grant"


class CookieSessionManager:
    def __init__(self, secure: bool = False) -> None:
        self.secure = secure

    def _attrs(self, max_age: int) -> str:
        attrs = f"Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"
        if self.secure:
            attrs += "; Secure"
        return attrs

    def issue(self, session_id: str, grant_id: str, access_max_age: int, refresh_max_age: int) -> tuple[str, str]:
        access = f"{ACCESS_COOKIE_NAME}={session_id}; {self._attrs(access_max_age)}"
        refresh = f"{REFRESH_COOKIE_NAME}={grant_id}; {self._attrs(refresh_max_age)}"
        return access, refresh

    def clear(self) -> tuple[str, str]:
        return (
            f"{ACCESS_COOKIE_NAME}=; {self._attrs(0)}",
            f"{REFRESH_COOKIE_NAME}=; {self._attrs(0)}",
        )

    def read(self, cookies: Mapping[str, str]) -> tuple[str | None, str | None]:
        return cookies.get(ACCESS_COOKIE_NAME) or None, cookies.get(REFRESH_COOKIE_NAME) or None

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from contextlib import AbstractContextManager

from src.application.workspace.ports import WorkspaceUnitOfWork
from src.domain.auth.entities import (
    AuthAuditEvent,
    AuthSession,
    EmailVerificationChallenge,
    RefreshGrant,
    UserAccount,
)


class AuthRepository(Protocol):
    def unit_of_work(self) -> AbstractContextManager[WorkspaceUnitOfWork]: ...

    def save_user(self, user: UserAccount, uow: WorkspaceUnitOfWork | None = None) -> None: ...

    def get_user_by_email(self, email: str) -> UserAccount | None: ...

    def get_user_by_email_or_id(self, key: str) -> UserAccount | None: ...

    def get_user_by_username(self, username: str) -> UserAccount | None: ...

    def save_challenge(self, challenge: EmailVerificationChallenge) -> None: ...

    def get_active_challenge(self, email: str, purpose: str) -> EmailVerificationChallenge | None: ...

    def save_session(self, session: AuthSession) -> None: ...

    def get_session(self, session_id: str) -> AuthSession | None: ...

    def get_session_by_grant(self, grant_id: str) -> AuthSession | None: ...

    def save_grant(self, grant: RefreshGrant) -> None: ...

    def get_grant(self, grant_id: str) -> RefreshGrant | None: ...

    def record_audit(self, event: AuthAuditEvent) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...

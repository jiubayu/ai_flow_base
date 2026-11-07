from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.auth.value_objects import (
    AuditEventType,
    ChallengeState,
    GrantState,
    SessionState,
)


@dataclass
class UserAccount:
    user_id: str
    email: str
    username: str
    password_hash: str
    password_hash_version: str
    created_at: datetime
    updated_at: datetime
    email_verified_at: datetime | None = None
    password_updated_at: datetime | None = None
    last_login_at: datetime | None = None

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    def mark_verified(self, now: datetime) -> None:
        if self.email_verified_at is not None:
            raise ValueError(f"邮箱 {self.email} 已验证，不能重复标记")
        self.email_verified_at = now
        self.password_updated_at = now
        self.updated_at = now

    def mark_login(self, now: datetime) -> None:
        self.last_login_at = now
        self.updated_at = now


@dataclass
class EmailVerificationChallenge:
    challenge_id: str
    email: str
    purpose: str
    code_digest: str
    expires_at: datetime
    sent_at: datetime
    created_at: datetime
    window_started_at: datetime
    window_send_count: int
    state: ChallengeState = ChallengeState.ACTIVE
    used_at: datetime | None = None
    invalidated_at: datetime | None = None
    verify_attempt_count: int = 0
    last_attempt_at: datetime | None = None

    max_attempts: int = field(default=5, init=False)

    def is_currently_valid(self, now: datetime) -> bool:
        return (
            self.state is ChallengeState.ACTIVE
            and now < self.expires_at
            and self.verify_attempt_count < self.max_attempts
        )

    def invalidate(self, now: datetime) -> None:
        if self.state is not ChallengeState.ACTIVE:
            raise ValueError(f"挑战 {self.challenge_id} 无法从 {self.state.value} 进入 REPLACED")
        self.state = ChallengeState.REPLACED
        self.invalidated_at = now

    def record_attempt(self, now: datetime) -> None:
        self.verify_attempt_count += 1
        self.last_attempt_at = now
        if self.verify_attempt_count >= self.max_attempts and self.state is ChallengeState.ACTIVE:
            self.state = ChallengeState.ATTEMPTS_EXHAUSTED

    def mark_used(self, now: datetime) -> None:
        if self.state is not ChallengeState.ACTIVE:
            raise ValueError(f"挑战 {self.challenge_id} 无法从 {self.state.value} 进入 USED")
        self.state = ChallengeState.USED
        self.used_at = now


@dataclass
class AuthSession:
    session_id: str
    user_id: str
    refresh_grant_id: str
    client_scope: str
    issued_at: datetime
    expires_at: datetime
    state: SessionState = SessionState.ACTIVE
    revoked_at: datetime | None = None
    last_seen_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return self.state is SessionState.ACTIVE and now < self.expires_at

    def mark_seen(self, now: datetime) -> None:
        self.last_seen_at = now

    def revoke(self, now: datetime) -> None:
        if self.state is not SessionState.ACTIVE:
            raise ValueError(f"会话 {self.session_id} 无法从 {self.state.value} 进入 REVOKED")
        self.state = SessionState.REVOKED
        self.revoked_at = now

    def replace(self, now: datetime) -> None:
        if self.state is not SessionState.ACTIVE:
            raise ValueError(f"会话 {self.session_id} 无法从 {self.state.value} 进入 REPLACED")
        self.state = SessionState.REPLACED


@dataclass
class RefreshGrant:
    refresh_grant_id: str
    user_id: str
    client_scope: str
    issued_at: datetime
    expires_at: datetime
    state: GrantState = GrantState.ACTIVE
    rotated_from_id: str | None = None
    revoked_at: datetime | None = None
    replaced_by_id: str | None = None
    last_used_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return self.state is GrantState.ACTIVE and now < self.expires_at

    def rotate_to(self, new_grant_id: str, now: datetime) -> None:
        if self.state is not GrantState.ACTIVE:
            raise ValueError(f"刷新资格 {self.refresh_grant_id} 无法从 {self.state.value} 进入 ROTATED")
        self.state = GrantState.ROTATED
        self.replaced_by_id = new_grant_id
        self.revoked_at = now
        self.last_used_at = now

    def revoke(self, now: datetime) -> None:
        if self.state is not GrantState.ACTIVE:
            raise ValueError(f"刷新资格 {self.refresh_grant_id} 无法从 {self.state.value} 进入 REVOKED")
        self.state = GrantState.REVOKED
        self.revoked_at = now


@dataclass
class AuthAuditEvent:
    event_id: str
    event_type: AuditEventType
    occurred_at: datetime
    outcome_code: str
    message: str
    user_id: str | None = None
    email: str | None = None
    client_scope: str | None = None

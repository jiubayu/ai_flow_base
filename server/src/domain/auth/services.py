from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime

from src.domain.auth.entities import EmailVerificationChallenge
from src.domain.auth.value_objects import check_password_policy


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def code_digest(email: str, code: str) -> str:
    import hashlib

    return hashlib.sha256(f"{email}:{code}".encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


@dataclass(frozen=True)
class RateLimitPolicy:
    min_interval_seconds: int
    window_seconds: int
    window_limit: int

    def evaluate(self, challenge: EmailVerificationChallenge | None, now: datetime) -> RateLimitDecision:
        if challenge is None:
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

        window_elapsed = (now - challenge.window_started_at).total_seconds()
        if window_elapsed >= self.window_seconds:
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

        interval_elapsed = (now - challenge.sent_at).total_seconds()
        if interval_elapsed < self.min_interval_seconds:
            return RateLimitDecision(
                allowed=False,
                retry_after_seconds=int(self.min_interval_seconds - interval_elapsed),
            )

        if challenge.window_send_count >= self.window_limit:
            return RateLimitDecision(
                allowed=False,
                retry_after_seconds=int(self.window_seconds - window_elapsed),
            )

        return RateLimitDecision(allowed=True, retry_after_seconds=0)


def password_policy_failure(password: str) -> str | None:
    return check_password_policy(password)

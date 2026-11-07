from datetime import datetime, timedelta, timezone

from src.domain.auth.entities import EmailVerificationChallenge
from src.domain.auth.services import RateLimitPolicy, code_digest, generate_verification_code
from src.domain.auth.value_objects import ChallengeState

POLICY = RateLimitPolicy(min_interval_seconds=60, window_seconds=900, window_limit=5)
NOW = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)


def _challenge(sent_at, window_started_at, window_send_count):
    return EmailVerificationChallenge(
        challenge_id="c1",
        email="user@example.com",
        purpose="register",
        code_digest="digest",
        expires_at=NOW,
        sent_at=sent_at,
        created_at=window_started_at,
        window_started_at=window_started_at,
        window_send_count=window_send_count,
    )


def test_generate_verification_code_is_six_digits():
    for _ in range(20):
        code = generate_verification_code()
        assert len(code) == 6 and code.isdigit()


def test_code_digest_is_deterministic_and_salted_by_email():
    assert code_digest("a@example.com", "123456") == code_digest("a@example.com", "123456")
    assert code_digest("a@example.com", "123456") != code_digest("a@example.com", "654321")
    assert code_digest("a@example.com", "123456") != code_digest("b@example.com", "123456")
    assert "123456" not in code_digest("a@example.com", "123456")


def test_first_send_allowed():
    decision = POLICY.evaluate(None, NOW)
    assert decision.allowed and decision.retry_after_seconds == 0


def test_send_within_min_interval_blocked():
    decision = POLICY.evaluate(_challenge(NOW, NOW, 1), NOW + timedelta(seconds=30))
    assert not decision.allowed
    assert decision.retry_after_seconds == 30


def test_window_limit_blocked():
    decision = POLICY.evaluate(_challenge(NOW, NOW, 5), NOW + timedelta(seconds=61))
    assert not decision.allowed
    assert decision.retry_after_seconds > 0


def test_new_window_allowed_after_window_elapsed():
    decision = POLICY.evaluate(_challenge(NOW, NOW, 5), NOW + timedelta(seconds=901))
    assert decision.allowed and decision.retry_after_seconds == 0

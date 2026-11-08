from datetime import datetime, timezone

import pytest

from src.application.auth.errors import EmailAlreadyRegisteredError
from src.domain.auth.entities import UserAccount
from src.infrastructure.persistence.auth_repository import PostgresAuthRepository

NOW = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)


def _user(user_id: str, email: str) -> UserAccount:
    return UserAccount(
        user_id=user_id,
        email=email,
        username=f"user-{user_id}",
        password_hash="hash",
        password_hash_version="scrypt",
        created_at=NOW,
        updated_at=NOW,
        password_updated_at=NOW,
        last_login_at=NOW,
    )


def test_duplicate_email_raises_domain_error(postgres_session_factory):
    repo = PostgresAuthRepository(postgres_session_factory)
    repo.save_user(_user("user-a", "duplicate@example.com"))

    with pytest.raises(EmailAlreadyRegisteredError):
        repo.save_user(_user("user-b", "duplicate@example.com"))

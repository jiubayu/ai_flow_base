from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.domain.auth.entities import AuthSession, RefreshGrant, UserAccount
from src.infrastructure.persistence.auth_repository import PostgresAuthRepository
from src.infrastructure.persistence.models import AuthSessionModel, RefreshGrantModel

NOW = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)
TTL = timedelta(days=14)


def _user() -> UserAccount:
    return UserAccount(
        user_id="user-1",
        email="rotation@example.com",
        username="rotation",
        password_hash="hash",
        password_hash_version="scrypt",
        created_at=NOW,
        updated_at=NOW,
        password_updated_at=NOW,
        last_login_at=NOW,
    )


def _grant(grant_id: str, rotated_from_id: str | None = None) -> RefreshGrant:
    return RefreshGrant(
        refresh_grant_id=grant_id,
        user_id="user-1",
        client_scope="browser",
        issued_at=NOW,
        expires_at=NOW + TTL,
        rotated_from_id=rotated_from_id,
    )


def _session(session_id: str, grant_id: str) -> AuthSession:
    return AuthSession(
        session_id=session_id,
        user_id="user-1",
        refresh_grant_id=grant_id,
        client_scope="browser",
        issued_at=NOW,
        expires_at=NOW + TTL,
    )


def test_rotate_session_writes_old_and_new_rows_in_one_transaction(postgres_session_factory):
    repo = PostgresAuthRepository(postgres_session_factory)
    repo.save_user(_user())
    old_grant = _grant("old-grant")
    old_session = _session("old-session", "old-grant")
    repo.save_grant(old_grant)
    repo.save_session(old_session)

    old_grant.rotate_to("new-grant", NOW)
    old_session.replace(NOW)
    new_grant = _grant("new-grant", rotated_from_id="old-grant")
    new_session = _session("new-session", "new-grant")

    repo.rotate_session(old_grant, old_session, new_grant, new_session)

    with postgres_session_factory() as session:
        stored_old_grant = session.scalar(
            select(RefreshGrantModel).where(RefreshGrantModel.refresh_grant_id == "old-grant")
        )
        stored_new_grant = session.scalar(
            select(RefreshGrantModel).where(RefreshGrantModel.refresh_grant_id == "new-grant")
        )
        stored_old_session = session.scalar(
            select(AuthSessionModel).where(AuthSessionModel.session_id == "old-session")
        )
        stored_new_session = session.scalar(
            select(AuthSessionModel).where(AuthSessionModel.session_id == "new-session")
        )

    assert stored_old_grant.state == "rotated"
    assert stored_old_grant.replaced_by_id == "new-grant"
    assert stored_new_grant is not None
    assert stored_new_grant.rotated_from_id == "old-grant"
    assert stored_old_session.state == "replaced"
    assert stored_new_session is not None


def test_rotate_session_rolls_back_when_a_write_fails(postgres_session_factory):
    repo = PostgresAuthRepository(postgres_session_factory)
    repo.save_user(_user())
    old_grant = _grant("old-grant-rollback")
    old_session = _session("old-session-rollback", "old-grant-rollback")
    repo.save_grant(old_grant)
    repo.save_session(old_session)

    # Pre-insert a duplicate PK so the new-grant write inside the transaction fails at flush.
    with postgres_session_factory.begin() as session:
        session.add(
            RefreshGrantModel(
                refresh_grant_id="new-grant-rollback",
                user_id="user-1",
                client_scope="browser",
                issued_at=NOW,
                expires_at=NOW + TTL,
                state="active",
            )
        )

    old_grant.rotate_to("new-grant-rollback", NOW)
    old_session.replace(NOW)
    new_grant = _grant("new-grant-rollback", rotated_from_id="old-grant-rollback")
    new_session = _session("new-session-rollback", "new-grant-rollback")

    with pytest.raises(IntegrityError):
        repo.rotate_session(old_grant, old_session, new_grant, new_session)

    with postgres_session_factory() as session:
        stored_old_grant = session.scalar(
            select(RefreshGrantModel).where(RefreshGrantModel.refresh_grant_id == "old-grant-rollback")
        )
        stored_old_session = session.scalar(
            select(AuthSessionModel).where(AuthSessionModel.session_id == "old-session-rollback")
        )
    assert stored_old_grant.state == "active"
    assert stored_old_grant.replaced_by_id is None
    assert stored_old_session.state == "active"

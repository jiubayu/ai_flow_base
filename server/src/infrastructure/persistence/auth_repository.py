from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.auth.entities import (
    AuthAuditEvent,
    AuthSession,
    EmailVerificationChallenge,
    RefreshGrant,
    UserAccount,
)
from src.domain.auth.value_objects import AuditEventType, ChallengeState, GrantState, SessionState
from src.infrastructure.persistence.auth_models import (
    AuthAuditEventRecord,
    AuthSessionRecord,
    EmailVerificationChallengeRecord,
    RefreshGrantRecord,
    UserAccountRecord,
)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class SqlAuthRepository:
    def __init__(self, engine, logger=None) -> None:
        self.engine = engine
        self.logger = logger

    @contextmanager
    def unit_of_work(self):
        from src.infrastructure.persistence.workspace_repository import SqlUnitOfWork

        conn = self.engine.connect()
        try:
            yield SqlUnitOfWork(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_user(self, user: UserAccount, uow=None) -> None:
        if uow is not None:
            uow.save_user(user)
            return

        with Session(self.engine) as session:
            record = session.get(UserAccountRecord, user.user_id)
            if record is None:
                record = UserAccountRecord(user_id=user.user_id)
            record.email = user.email
            record.username = user.username
            record.email_verified_at = _iso(user.email_verified_at)
            record.password_hash = user.password_hash
            record.password_hash_version = user.password_hash_version
            record.password_updated_at = _iso(user.password_updated_at)
            record.created_at = _iso(user.created_at)
            record.updated_at = _iso(user.updated_at)
            record.last_login_at = _iso(user.last_login_at)
            session.add(record)
            session.commit()

    def get_user_by_email(self, email: str) -> UserAccount | None:
        with Session(self.engine) as session:
            record = session.scalar(select(UserAccountRecord).where(UserAccountRecord.email == email))
            return self._to_user(record) if record else None

    def get_user_by_email_or_id(self, key: str) -> UserAccount | None:
        with Session(self.engine) as session:
            record = session.get(UserAccountRecord, key)
            if record is None:
                record = session.scalar(select(UserAccountRecord).where(UserAccountRecord.email == key))
            return self._to_user(record) if record else None

    def get_user_by_username(self, username: str) -> UserAccount | None:
        with Session(self.engine) as session:
            record = session.scalar(select(UserAccountRecord).where(UserAccountRecord.username == username))
            return self._to_user(record) if record else None

    def _to_user(self, record: UserAccountRecord) -> UserAccount:
        return UserAccount(
            user_id=record.user_id,
            email=record.email,
            username=record.username,
            password_hash=record.password_hash,
            password_hash_version=record.password_hash_version,
            created_at=_parse(record.created_at),
            updated_at=_parse(record.updated_at),
            email_verified_at=_parse(record.email_verified_at),
            password_updated_at=_parse(record.password_updated_at),
            last_login_at=_parse(record.last_login_at),
        )

    def save_challenge(self, challenge: EmailVerificationChallenge) -> None:
        with Session(self.engine) as session:
            record = session.get(EmailVerificationChallengeRecord, challenge.challenge_id)
            if record is None:
                record = EmailVerificationChallengeRecord(challenge_id=challenge.challenge_id)
            record.email = challenge.email
            record.purpose = challenge.purpose
            record.code_digest = challenge.code_digest
            record.expires_at = _iso(challenge.expires_at)
            record.sent_at = _iso(challenge.sent_at)
            record.used_at = _iso(challenge.used_at)
            record.invalidated_at = _iso(challenge.invalidated_at)
            record.window_started_at = _iso(challenge.window_started_at)
            record.window_send_count = challenge.window_send_count
            record.verify_attempt_count = challenge.verify_attempt_count
            record.last_attempt_at = _iso(challenge.last_attempt_at)
            record.created_at = _iso(challenge.created_at)
            record.state = challenge.state.value
            session.add(record)
            session.commit()

    def get_active_challenge(self, email: str, purpose: str) -> EmailVerificationChallenge | None:
        with Session(self.engine) as session:
            record = session.scalar(
                select(EmailVerificationChallengeRecord)
                .where(
                    EmailVerificationChallengeRecord.email == email,
                    EmailVerificationChallengeRecord.purpose == purpose,
                    EmailVerificationChallengeRecord.state == ChallengeState.ACTIVE.value,
                )
                .order_by(EmailVerificationChallengeRecord.created_at.desc())
                .limit(1)
            )
            return self._to_challenge(record) if record else None

    def _to_challenge(self, record: EmailVerificationChallengeRecord) -> EmailVerificationChallenge:
        return EmailVerificationChallenge(
            challenge_id=record.challenge_id,
            email=record.email,
            purpose=record.purpose,
            code_digest=record.code_digest,
            expires_at=_parse(record.expires_at),
            sent_at=_parse(record.sent_at),
            created_at=_parse(record.created_at),
            window_started_at=_parse(record.window_started_at),
            window_send_count=record.window_send_count,
            state=ChallengeState(record.state),
            used_at=_parse(record.used_at),
            invalidated_at=_parse(record.invalidated_at),
            verify_attempt_count=record.verify_attempt_count,
            last_attempt_at=_parse(record.last_attempt_at),
        )

    def save_session(self, session_obj: AuthSession) -> None:
        with Session(self.engine) as session:
            record = session.get(AuthSessionRecord, session_obj.session_id)
            if record is None:
                record = AuthSessionRecord(session_id=session_obj.session_id)
            record.user_id = session_obj.user_id
            record.refresh_grant_id = session_obj.refresh_grant_id
            record.client_scope = session_obj.client_scope
            record.issued_at = _iso(session_obj.issued_at)
            record.expires_at = _iso(session_obj.expires_at)
            record.revoked_at = _iso(session_obj.revoked_at)
            record.last_seen_at = _iso(session_obj.last_seen_at)
            record.state = session_obj.state.value
            session.add(record)
            session.commit()

    def get_session(self, session_id: str) -> AuthSession | None:
        with Session(self.engine) as session:
            record = session.get(AuthSessionRecord, session_id)
            return self._to_session(record) if record else None

    def get_session_by_grant(self, grant_id: str) -> AuthSession | None:
        with Session(self.engine) as session:
            record = session.scalar(
                select(AuthSessionRecord)
                .where(AuthSessionRecord.refresh_grant_id == grant_id)
                .order_by(AuthSessionRecord.issued_at.desc())
                .limit(1)
            )
            return self._to_session(record) if record else None

    def _to_session(self, record: AuthSessionRecord) -> AuthSession:
        return AuthSession(
            session_id=record.session_id,
            user_id=record.user_id,
            refresh_grant_id=record.refresh_grant_id,
            client_scope=record.client_scope,
            issued_at=_parse(record.issued_at),
            expires_at=_parse(record.expires_at),
            state=SessionState(record.state),
            revoked_at=_parse(record.revoked_at),
            last_seen_at=_parse(record.last_seen_at),
        )

    def save_grant(self, grant: RefreshGrant) -> None:
        with Session(self.engine) as session:
            record = session.get(RefreshGrantRecord, grant.refresh_grant_id)
            if record is None:
                record = RefreshGrantRecord(refresh_grant_id=grant.refresh_grant_id)
            record.user_id = grant.user_id
            record.client_scope = grant.client_scope
            record.rotated_from_id = grant.rotated_from_id
            record.issued_at = _iso(grant.issued_at)
            record.expires_at = _iso(grant.expires_at)
            record.revoked_at = _iso(grant.revoked_at)
            record.replaced_by_id = grant.replaced_by_id
            record.last_used_at = _iso(grant.last_used_at)
            record.state = grant.state.value
            session.add(record)
            session.commit()

    def get_grant(self, grant_id: str) -> RefreshGrant | None:
        with Session(self.engine) as session:
            record = session.get(RefreshGrantRecord, grant_id)
            return self._to_grant(record) if record else None

    def _to_grant(self, record: RefreshGrantRecord) -> RefreshGrant:
        return RefreshGrant(
            refresh_grant_id=record.refresh_grant_id,
            user_id=record.user_id,
            client_scope=record.client_scope,
            rotated_from_id=record.rotated_from_id,
            issued_at=_parse(record.issued_at),
            expires_at=_parse(record.expires_at),
            state=GrantState(record.state),
            revoked_at=_parse(record.revoked_at),
            replaced_by_id=record.replaced_by_id,
            last_used_at=_parse(record.last_used_at),
        )

    def record_audit(self, event: AuthAuditEvent) -> None:
        with Session(self.engine) as session:
            record = AuthAuditEventRecord(
                event_id=event.event_id,
                event_type=event.event_type.value,
                user_id=event.user_id,
                email=event.email,
                client_scope=event.client_scope,
                occurred_at=_iso(event.occurred_at),
                outcome_code=event.outcome_code,
                message=event.message,
            )
            session.add(record)
            session.commit()

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from src.application.auth.errors import AuthError, EmailAlreadyRegisteredError
from src.domain.auth.entities import (
    AuthAuditEvent,
    AuthSession,
    EmailVerificationChallenge,
    RefreshGrant,
    UserAccount,
)
from src.domain.auth.value_objects import ChallengeState, GrantState, SessionState
from src.infrastructure.persistence.models import (
    AuthAuditEventModel,
    AuthSessionModel,
    EmailVerificationChallengeModel,
    RefreshGrantModel,
    UserAccountModel,
)
from src.infrastructure.persistence.workspace_repository import PostgresUnitOfWork


class PostgresAuthRepository:
    def __init__(self, session_factory, logger=None) -> None:
        self._session_factory = session_factory
        self.logger = logger

    @contextmanager
    def unit_of_work(self):
        with self._session_factory.begin() as session:
            yield PostgresUnitOfWork(session)

    def save_user(self, user: UserAccount, uow=None) -> None:
        if uow is not None:
            uow.save_user(user)
            return

        try:
            with self._session_factory.begin() as session:
                record = session.get(UserAccountModel, user.user_id)
                if record is None:
                    record = UserAccountModel(user_id=user.user_id)
                record.email = user.email
                record.username = user.username
                record.email_verified_at = user.email_verified_at
                record.password_hash = user.password_hash
                record.password_hash_version = user.password_hash_version
                record.password_updated_at = user.password_updated_at
                record.created_at = user.created_at
                record.updated_at = user.updated_at
                record.last_login_at = user.last_login_at
                session.add(record)
        except IntegrityError as exc:
            # 只有唯一约束冲突才是"已被注册"；其他完整性错误原样抛出。
            if getattr(exc.orig, "sqlstate", None) != "23505":
                raise
            raise EmailAlreadyRegisteredError(f"邮箱已被注册：{user.email}") from exc

    def get_user_by_email(self, email: str) -> UserAccount | None:
        with self._session_factory() as session:
            record = session.scalar(select(UserAccountModel).where(UserAccountModel.email == email))
            return self._to_user(record) if record else None

    def get_user_by_email_or_id(self, key: str) -> UserAccount | None:
        with self._session_factory() as session:
            record = session.get(UserAccountModel, key)
            if record is None:
                record = session.scalar(select(UserAccountModel).where(UserAccountModel.email == key))
            return self._to_user(record) if record else None

    def get_user_by_username(self, username: str) -> UserAccount | None:
        with self._session_factory() as session:
            record = session.scalar(select(UserAccountModel).where(UserAccountModel.username == username))
            return self._to_user(record) if record else None

    def _to_user(self, record: UserAccountModel) -> UserAccount:
        return UserAccount(
            user_id=record.user_id,
            email=record.email,
            username=record.username,
            password_hash=record.password_hash,
            password_hash_version=record.password_hash_version,
            created_at=record.created_at,
            updated_at=record.updated_at,
            email_verified_at=record.email_verified_at,
            password_updated_at=record.password_updated_at,
            last_login_at=record.last_login_at,
        )

    def save_challenge(self, challenge: EmailVerificationChallenge) -> None:
        with self._session_factory.begin() as session:
            record = session.get(EmailVerificationChallengeModel, challenge.challenge_id)
            if record is None:
                record = EmailVerificationChallengeModel(challenge_id=challenge.challenge_id)
            record.email = challenge.email
            record.purpose = challenge.purpose
            record.code_digest = challenge.code_digest
            record.expires_at = challenge.expires_at
            record.sent_at = challenge.sent_at
            record.used_at = challenge.used_at
            record.invalidated_at = challenge.invalidated_at
            record.window_started_at = challenge.window_started_at
            record.window_send_count = challenge.window_send_count
            record.verify_attempt_count = challenge.verify_attempt_count
            record.last_attempt_at = challenge.last_attempt_at
            record.created_at = challenge.created_at
            record.state = challenge.state.value
            session.add(record)

    def get_active_challenge(self, email: str, purpose: str) -> EmailVerificationChallenge | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(EmailVerificationChallengeModel)
                .where(
                    EmailVerificationChallengeModel.email == email,
                    EmailVerificationChallengeModel.purpose == purpose,
                    EmailVerificationChallengeModel.state == ChallengeState.ACTIVE.value,
                )
                .order_by(EmailVerificationChallengeModel.created_at.desc())
                .limit(1)
            )
            return self._to_challenge(record) if record else None

    def _to_challenge(self, record: EmailVerificationChallengeModel) -> EmailVerificationChallenge:
        return EmailVerificationChallenge(
            challenge_id=record.challenge_id,
            email=record.email,
            purpose=record.purpose,
            code_digest=record.code_digest,
            expires_at=record.expires_at,
            sent_at=record.sent_at,
            created_at=record.created_at,
            window_started_at=record.window_started_at,
            window_send_count=record.window_send_count,
            state=ChallengeState(record.state),
            used_at=record.used_at,
            invalidated_at=record.invalidated_at,
            verify_attempt_count=record.verify_attempt_count,
            last_attempt_at=record.last_attempt_at,
        )

    def save_session(self, session_obj: AuthSession) -> None:
        with self._session_factory.begin() as session:
            record = session.get(AuthSessionModel, session_obj.session_id)
            if record is None:
                record = AuthSessionModel(session_id=session_obj.session_id)
            record.user_id = session_obj.user_id
            record.refresh_grant_id = session_obj.refresh_grant_id
            record.client_scope = session_obj.client_scope
            record.issued_at = session_obj.issued_at
            record.expires_at = session_obj.expires_at
            record.revoked_at = session_obj.revoked_at
            record.last_seen_at = session_obj.last_seen_at
            record.state = session_obj.state.value
            session.add(record)

    def get_session(self, session_id: str) -> AuthSession | None:
        with self._session_factory() as session:
            record = session.get(AuthSessionModel, session_id)
            return self._to_session(record) if record else None

    def get_session_by_grant(self, grant_id: str) -> AuthSession | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(AuthSessionModel)
                .where(AuthSessionModel.refresh_grant_id == grant_id)
                .order_by(AuthSessionModel.issued_at.desc())
                .limit(1)
            )
            return self._to_session(record) if record else None

    def _to_session(self, record: AuthSessionModel) -> AuthSession:
        return AuthSession(
            session_id=record.session_id,
            user_id=record.user_id,
            refresh_grant_id=record.refresh_grant_id,
            client_scope=record.client_scope,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            state=SessionState(record.state),
            revoked_at=record.revoked_at,
            last_seen_at=record.last_seen_at,
        )

    def save_grant(self, grant: RefreshGrant) -> None:
        with self._session_factory.begin() as session:
            record = session.get(RefreshGrantModel, grant.refresh_grant_id)
            if record is None:
                record = RefreshGrantModel(refresh_grant_id=grant.refresh_grant_id)
            record.user_id = grant.user_id
            record.client_scope = grant.client_scope
            record.rotated_from_id = grant.rotated_from_id
            record.issued_at = grant.issued_at
            record.expires_at = grant.expires_at
            record.revoked_at = grant.revoked_at
            record.replaced_by_id = grant.replaced_by_id
            record.last_used_at = grant.last_used_at
            record.state = grant.state.value
            session.add(record)

    def get_grant(self, grant_id: str) -> RefreshGrant | None:
        with self._session_factory() as session:
            record = session.get(RefreshGrantModel, grant_id)
            return self._to_grant(record) if record else None

    def _to_grant(self, record: RefreshGrantModel) -> RefreshGrant:
        return RefreshGrant(
            refresh_grant_id=record.refresh_grant_id,
            user_id=record.user_id,
            client_scope=record.client_scope,
            rotated_from_id=record.rotated_from_id,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            state=GrantState(record.state),
            revoked_at=record.revoked_at,
            replaced_by_id=record.replaced_by_id,
            last_used_at=record.last_used_at,
        )

    def rotate_session(
        self,
        old_grant: RefreshGrant,
        old_session: AuthSession | None,
        new_grant: RefreshGrant,
        new_session: AuthSession,
    ) -> None:
        try:
            with self._session_factory.begin() as session:
                session.execute(
                    update(RefreshGrantModel)
                    .where(RefreshGrantModel.refresh_grant_id == old_grant.refresh_grant_id)
                    .values(
                        state=old_grant.state.value,
                        revoked_at=old_grant.revoked_at,
                        replaced_by_id=old_grant.replaced_by_id,
                        last_used_at=old_grant.last_used_at,
                    )
                )
                if old_session is not None:
                    session.execute(
                        update(AuthSessionModel)
                        .where(AuthSessionModel.session_id == old_session.session_id)
                        .values(
                            state=old_session.state.value,
                            revoked_at=old_session.revoked_at,
                            last_seen_at=old_session.last_seen_at,
                        )
                    )
                session.add(_grant_model(new_grant))
                # 两个模型之间没有 relationship，flush 的拓扑排序无法保证父表先插入；显式 flush 确保 grant 先于 session 落库。
                session.flush()
                session.add(_session_model(new_session))
        except IntegrityError as exc:
            raise AuthError("会话轮换写入冲突") from exc

    def record_audit(self, event: AuthAuditEvent) -> None:
        with self._session_factory.begin() as session:
            session.add(
                AuthAuditEventModel(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    user_id=event.user_id,
                    email=event.email,
                    client_scope=event.client_scope,
                    occurred_at=event.occurred_at,
                    outcome_code=event.outcome_code,
                    message=event.message,
                )
            )


def _grant_model(grant: RefreshGrant) -> RefreshGrantModel:
    return RefreshGrantModel(
        refresh_grant_id=grant.refresh_grant_id,
        user_id=grant.user_id,
        client_scope=grant.client_scope,
        rotated_from_id=grant.rotated_from_id,
        issued_at=grant.issued_at,
        expires_at=grant.expires_at,
        revoked_at=grant.revoked_at,
        replaced_by_id=grant.replaced_by_id,
        last_used_at=grant.last_used_at,
        state=grant.state.value,
    )


def _session_model(session_obj: AuthSession) -> AuthSessionModel:
    return AuthSessionModel(
        session_id=session_obj.session_id,
        user_id=session_obj.user_id,
        refresh_grant_id=session_obj.refresh_grant_id,
        client_scope=session_obj.client_scope,
        issued_at=session_obj.issued_at,
        expires_at=session_obj.expires_at,
        revoked_at=session_obj.revoked_at,
        last_seen_at=session_obj.last_seen_at,
        state=session_obj.state.value,
    )

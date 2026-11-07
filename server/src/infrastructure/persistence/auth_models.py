from __future__ import annotations

from sqlalchemy import Column, Index, Integer, String, Text

from src.infrastructure.persistence.result_store import Base


class UserAccountRecord(Base):
    __tablename__ = "user_accounts"

    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(String)
    email_verified_at = Column(Text)
    password_hash = Column(Text, nullable=False)
    password_hash_version = Column(String, nullable=False)
    password_updated_at = Column(Text)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    last_login_at = Column(Text)


class EmailVerificationChallengeRecord(Base):
    __tablename__ = "email_verification_challenges"

    challenge_id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    code_digest = Column(String, nullable=False)
    expires_at = Column(Text, nullable=False)
    sent_at = Column(Text, nullable=False)
    used_at = Column(Text)
    invalidated_at = Column(Text)
    window_started_at = Column(Text, nullable=False)
    window_send_count = Column(Integer, nullable=False)
    verify_attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(Text)
    created_at = Column(Text, nullable=False)
    state = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_challenges_email_purpose_state", "email", "purpose", "state"),
    )


class AuthSessionRecord(Base):
    __tablename__ = "auth_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    refresh_grant_id = Column(String, nullable=False)
    client_scope = Column(String, nullable=False)
    issued_at = Column(Text, nullable=False)
    expires_at = Column(Text, nullable=False)
    revoked_at = Column(Text)
    last_seen_at = Column(Text)
    state = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_auth_sessions_grant", "refresh_grant_id"),
    )


class RefreshGrantRecord(Base):
    __tablename__ = "refresh_grants"

    refresh_grant_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    client_scope = Column(String, nullable=False)
    rotated_from_id = Column(String)
    issued_at = Column(Text, nullable=False)
    expires_at = Column(Text, nullable=False)
    revoked_at = Column(Text)
    replaced_by_id = Column(String)
    last_used_at = Column(Text)
    state = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_refresh_grants_user_scope_state", "user_id", "client_scope", "state"),
    )


class AuthAuditEventRecord(Base):
    __tablename__ = "auth_audit_events"

    event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    user_id = Column(String)
    email = Column(String)
    client_scope = Column(String)
    occurred_at = Column(Text, nullable=False)
    outcome_code = Column(String, nullable=False)
    message = Column(Text, nullable=False)

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, inspect

AUTH_TABLES = (
    "user_accounts",
    "email_verification_challenges",
    "auth_sessions",
    "refresh_grants",
    "auth_audit_events",
)

MIGRATION_DDL = (
    """
    CREATE TABLE IF NOT EXISTS user_accounts (
        user_id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        email_verified_at TEXT,
        password_hash TEXT NOT NULL,
        password_hash_version TEXT NOT NULL,
        password_updated_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_login_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS email_verification_challenges (
        challenge_id TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        purpose TEXT NOT NULL,
        code_digest TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        used_at TEXT,
        invalidated_at TEXT,
        window_started_at TEXT NOT NULL,
        window_send_count INTEGER NOT NULL,
        verify_attempt_count INTEGER NOT NULL DEFAULT 0,
        last_attempt_at TEXT,
        created_at TEXT NOT NULL,
        state TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS auth_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        refresh_grant_id TEXT NOT NULL,
        client_scope TEXT NOT NULL,
        issued_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        revoked_at TEXT,
        last_seen_at TEXT,
        state TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS refresh_grants (
        refresh_grant_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        client_scope TEXT NOT NULL,
        rotated_from_id TEXT,
        issued_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        revoked_at TEXT,
        replaced_by_id TEXT,
        last_used_at TEXT,
        state TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS auth_audit_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        user_id TEXT,
        email TEXT,
        client_scope TEXT,
        occurred_at TEXT NOT NULL,
        outcome_code TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_user_accounts_email ON user_accounts (email)",
    "CREATE INDEX IF NOT EXISTS ix_challenges_email_purpose_state ON email_verification_challenges (email, purpose, state)",
    "CREATE INDEX IF NOT EXISTS ix_auth_sessions_grant ON auth_sessions (refresh_grant_id)",
    "CREATE INDEX IF NOT EXISTS ix_refresh_grants_user_scope_state ON refresh_grants (user_id, client_scope, state)",
)


def run_migrations(db_path: Path, logger: logging.Logger | None = None) -> list[str]:
    """幂等执行认证 schema 迁移；重复执行不会报重复建表错误。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    created: list[str] = []
    existing = set(inspect(engine).get_table_names())
    with engine.begin() as conn:
        for ddl in MIGRATION_DDL:
            conn.exec_driver_sql(ddl)
            table = ddl.split(" IF NOT EXISTS ", 1)[1].split("(", 1)[0].strip()
            if table not in existing:
                created.append(table)
    if logger is not None:
        logger.info(f"认证迁移完成：{db_path}；本次新建表：{created or '无（全部已存在）'}")
    return created


def verify_migration(db_path: Path) -> list[str]:
    """检查表与关键索引是否存在，返回缺失项；空列表表示验证通过。"""
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    inspector = inspect(engine)
    missing: list[str] = []
    tables = set(inspector.get_table_names())
    for table in AUTH_TABLES:
        if table not in tables:
            missing.append(f"table:{table}")
    indexes = {i["name"] for i in inspector.get_indexes("user_accounts")}
    if "ux_user_accounts_email" not in indexes:
        missing.append("index:ux_user_accounts_email")
    columns = {c["name"] for c in inspector.get_columns("email_verification_challenges")}
    for column in ("code_digest", "window_started_at", "window_send_count"):
        if column not in columns:
            missing.append(f"column:email_verification_challenges.{column}")
    return missing

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, inspect, text

WORKSPACE_TABLES = (
    "workspaces",
    "workspace_memberships",
    "user_workspace_preferences",
    "workspace_audit_events",
    "workspace_applications",
)

MIGRATION_DDL = (
    """
    CREATE TABLE IF NOT EXISTS workspaces (
        workspace_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_by_user_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workspace_memberships (
        membership_id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        status TEXT NOT NULL,
        joined_at TEXT NOT NULL,
        removed_at TEXT,
        created_by_user_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_workspace_preferences (
        user_id TEXT PRIMARY KEY,
        last_workspace_id TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workspace_audit_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        workspace_id TEXT,
        actor_user_id TEXT,
        target_user_id TEXT,
        outcome_code TEXT NOT NULL,
        message TEXT NOT NULL,
        occurred_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workspace_applications (
        application_id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        owner_user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_memberships_active ON workspace_memberships (workspace_id, user_id) WHERE status = 'active'",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_workspace_applications_name ON workspace_applications (workspace_id, name)",
    "CREATE INDEX IF NOT EXISTS ix_workspace_applications_workspace ON workspace_applications (workspace_id, updated_at)",
    "CREATE INDEX IF NOT EXISTS ix_memberships_user_status ON workspace_memberships (user_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_memberships_workspace_status_role ON workspace_memberships (workspace_id, status, role)",
    "CREATE INDEX IF NOT EXISTS ix_workspace_audit_workspace_occurred ON workspace_audit_events (workspace_id, occurred_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_user_accounts_username ON user_accounts (username)",
)

VALIDATION_SQL = {
    "users_without_active_membership": """
        SELECT COUNT(*) FROM user_accounts
        WHERE user_id NOT IN (
            SELECT user_id FROM workspace_memberships WHERE status = 'active'
        )
    """,
    "workspaces_without_manager": """
        SELECT COUNT(*) FROM workspaces
        WHERE workspace_id NOT IN (
            SELECT workspace_id FROM workspace_memberships
            WHERE status = 'active' AND role = 'manager'
        )
    """,
    "duplicate_active_memberships": """
        SELECT COUNT(*) FROM (
            SELECT workspace_id, user_id, COUNT(*) AS c
            FROM workspace_memberships
            WHERE status = 'active'
            GROUP BY workspace_id, user_id
            HAVING COUNT(*) > 1
        )
    """,
    "users_without_username": """
        SELECT COUNT(*) FROM user_accounts WHERE username IS NULL
    """,
    "preferences_pointing_to_inaccessible_workspace": """
        SELECT COUNT(*) FROM user_workspace_preferences p
        WHERE p.last_workspace_id NOT IN (
            SELECT workspace_id FROM workspace_memberships
            WHERE status = 'active' AND user_id = p.user_id
        )
    """,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_username_column(engine, logger: logging.Logger | None = None) -> bool:
    """幂等添加 user_accounts.username；已存在时不重复执行。"""
    columns = {c["name"] for c in inspect(engine).get_columns("user_accounts")}
    if "username" in columns:
        return False
    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER TABLE user_accounts ADD COLUMN username TEXT")
    if logger is not None:
        logger.info("数据升级：user_accounts 新增 username 列（存量行为 NULL，由回填补齐）")
    return True


def backfill_usernames(engine, logger: logging.Logger | None = None) -> int:
    """为存量用户按邮箱前缀补齐 username；冲突时追加序号，只处理 NULL 记录。"""
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT user_id, email FROM user_accounts WHERE username IS NULL ORDER BY created_at")
        ).fetchall()
        if not rows:
            return 0
        taken = {
            row[0]
            for row in conn.execute(text("SELECT username FROM user_accounts WHERE username IS NOT NULL"))
        }
        filled = 0
        for user_id, email in rows:
            base = email.split("@", 1)[0].strip().lower() or "user"
            candidate = base
            suffix = 1
            while candidate in taken:
                candidate = f"{base}{suffix}"
                suffix += 1
            taken.add(candidate)
            conn.execute(
                text("UPDATE user_accounts SET username = :username WHERE user_id = :user_id"),
                {"username": candidate, "user_id": user_id},
            )
            filled += 1
        if logger is not None and filled:
            logger.info(f"数据升级：为 {filled} 个存量用户补齐 username")
        return filled


def backfill_default_workspaces(engine, logger: logging.Logger | None = None) -> int:
    """为尚无工作空间的存量用户创建默认工作空间、管理者成员关系与偏好；幂等。"""
    now = _now_iso()
    with engine.begin() as conn:
        users = conn.execute(
            text(
                """
                SELECT user_id, username FROM user_accounts
                WHERE user_id NOT IN (
                    SELECT user_id FROM workspace_memberships WHERE status = 'active'
                )
                ORDER BY created_at
                """
            )
        ).fetchall()
        if not users:
            return 0
        created = 0
        for user_id, username in users:
            label = username or user_id
            workspace_id = str(uuid4())
            conn.execute(
                text(
                    "INSERT INTO workspaces (workspace_id, name, created_by_user_id, created_at, updated_at, status) "
                    "VALUES (:workspace_id, :name, :created_by, :created_at, :updated_at, 'active')"
                ),
                {
                    "workspace_id": workspace_id,
                    "name": f"{label} 的工作空间",
                    "created_by": user_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            conn.execute(
                text(
                    "INSERT INTO workspace_memberships (membership_id, workspace_id, user_id, role, status, "
                    "joined_at, removed_at, created_by_user_id, created_at, updated_at) "
                    "VALUES (:membership_id, :workspace_id, :user_id, 'manager', 'active', :joined_at, NULL, NULL, :created_at, :updated_at)"
                ),
                {
                    "membership_id": str(uuid4()),
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "joined_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            conn.execute(
                text(
                    "INSERT INTO user_workspace_preferences (user_id, last_workspace_id, updated_at) "
                    "VALUES (:user_id, :last_workspace_id, :updated_at) "
                    "ON CONFLICT (user_id) DO UPDATE SET last_workspace_id = :last_workspace_id, updated_at = :updated_at"
                ),
                {"user_id": user_id, "last_workspace_id": workspace_id, "updated_at": now},
            )
            created += 1
        if logger is not None and created:
            logger.info(f"数据升级：为 {created} 个存量用户创建默认工作空间与管理者成员关系")
        return created


def run_migrations(db_path: Path, logger: logging.Logger | None = None) -> list[str]:
    """幂等执行工作空间 schema 迁移；重复执行不会报重复建表错误。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    existing = set(inspect(engine).get_table_names())
    ensure_username_column(engine, logger)
    created: list[str] = []
    with engine.begin() as conn:
        for ddl in MIGRATION_DDL:
            conn.exec_driver_sql(ddl)
            table = ddl.split(" IF NOT EXISTS ", 1)[1].split("(", 1)[0].strip()
            if table not in existing:
                created.append(table)
    backfill_usernames(engine, logger)
    backfill_default_workspaces(engine, logger)
    if logger is not None:
        logger.info(f"工作空间迁移完成：{db_path}；本次新建表：{created or '无（全部已存在）'}")
    return created


def verify_migration(db_path: Path) -> list[str]:
    """检查工作空间表、关键索引与 username 列是否存在，返回缺失项。"""
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    inspector = inspect(engine)
    missing: list[str] = []
    tables = set(inspector.get_table_names())
    for table in WORKSPACE_TABLES:
        if table not in tables:
            missing.append(f"table:{table}")
    if "username" not in {c["name"] for c in inspector.get_columns("user_accounts")}:
        missing.append("column:user_accounts.username")
    indexes = {i["name"] for i in inspector.get_indexes("workspace_memberships")}
    if "ux_memberships_active" not in indexes:
        missing.append("index:ux_memberships_active")
    app_indexes = {i["name"] for i in inspector.get_indexes("workspace_applications")}
    if "ux_workspace_applications_name" not in app_indexes:
        missing.append("index:ux_workspace_applications_name")
    return missing


def run_validation_queries(engine) -> dict[str, int]:
    """执行数据升级验证 SQL，返回各项异常计数；全为 0 表示验证通过。"""
    results: dict[str, int] = {}
    with engine.begin() as conn:
        for name, sql in VALIDATION_SQL.items():
            results[name] = conn.execute(text(sql)).fetchone()[0]
    return results

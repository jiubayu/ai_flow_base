from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from src.application.workspace.ports import WorkspaceMemberView, WorkspaceUnitOfWork
from src.domain.auth.entities import UserAccount
from src.domain.workspace.entities import (
    UserWorkspacePreference,
    Workspace,
    WorkspaceApplication,
    WorkspaceAuditEvent,
    WorkspaceMembership,
)
from src.domain.workspace.value_objects import (
    ApplicationStatus,
    MembershipStatus,
    WorkspaceEventType,
    WorkspaceRole,
    WorkspaceStatus,
)
from src.infrastructure.persistence.workspace_migrations import run_migrations


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class SqlUnitOfWork(WorkspaceUnitOfWork):
    """注册相关写入的原子边界：用户、工作空间、成员关系与偏好必须一起提交或一起回滚。"""

    def __init__(self, conn) -> None:
        self.conn = conn

    def save_user(self, user: UserAccount) -> None:
        self.conn.execute(
            text(
                "INSERT INTO user_accounts (user_id, email, username, email_verified_at, password_hash, "
                "password_hash_version, password_updated_at, created_at, updated_at, last_login_at) "
                "VALUES (:user_id, :email, :username, :email_verified_at, :password_hash, :password_hash_version, "
                ":password_updated_at, :created_at, :updated_at, :last_login_at) "
                "ON CONFLICT (user_id) DO UPDATE SET username = excluded.username, updated_at = excluded.updated_at"
            ),
            {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "email_verified_at": _iso(user.email_verified_at),
                "password_hash": user.password_hash,
                "password_hash_version": user.password_hash_version,
                "password_updated_at": _iso(user.password_updated_at),
                "created_at": _iso(user.created_at),
                "updated_at": _iso(user.updated_at),
                "last_login_at": _iso(user.last_login_at),
            },
        )

    def save_workspace(self, workspace: Workspace) -> None:
        self.conn.execute(
            text(
                "INSERT INTO workspaces (workspace_id, name, created_by_user_id, created_at, updated_at, status) "
                "VALUES (:workspace_id, :name, :created_by_user_id, :created_at, :updated_at, :status) "
                "ON CONFLICT (workspace_id) DO UPDATE SET name = excluded.name, updated_at = excluded.updated_at"
            ),
            {
                "workspace_id": workspace.workspace_id,
                "name": workspace.name,
                "created_by_user_id": workspace.created_by_user_id,
                "created_at": _iso(workspace.created_at),
                "updated_at": _iso(workspace.updated_at),
                "status": workspace.status.value,
            },
        )

    def save_membership(self, membership: WorkspaceMembership) -> None:
        self.conn.execute(
            text(
                "INSERT INTO workspace_memberships (membership_id, workspace_id, user_id, role, status, joined_at, "
                "removed_at, created_by_user_id, created_at, updated_at) "
                "VALUES (:membership_id, :workspace_id, :user_id, :role, :status, :joined_at, :removed_at, "
                ":created_by_user_id, :created_at, :updated_at) "
                "ON CONFLICT (membership_id) DO UPDATE SET role = excluded.role, status = excluded.status, "
                "removed_at = excluded.removed_at, updated_at = excluded.updated_at"
            ),
            {
                "membership_id": membership.membership_id,
                "workspace_id": membership.workspace_id,
                "user_id": membership.user_id,
                "role": membership.role.value,
                "status": membership.status.value,
                "joined_at": _iso(membership.joined_at),
                "removed_at": _iso(membership.removed_at),
                "created_by_user_id": membership.created_by_user_id,
                "created_at": _iso(membership.created_at),
                "updated_at": _iso(membership.updated_at),
            },
        )

    def save_preference(self, preference: UserWorkspacePreference) -> None:
        self.conn.execute(
            text(
                "INSERT INTO user_workspace_preferences (user_id, last_workspace_id, updated_at) "
                "VALUES (:user_id, :last_workspace_id, :updated_at) "
                "ON CONFLICT (user_id) DO UPDATE SET last_workspace_id = excluded.last_workspace_id, "
                "updated_at = excluded.updated_at"
            ),
            {
                "user_id": preference.user_id,
                "last_workspace_id": preference.last_workspace_id,
                "updated_at": _iso(preference.updated_at),
            },
        )

    def save_application(self, application: WorkspaceApplication) -> None:
        self.conn.execute(_APPLICATION_UPSERT, _application_params(application))

    def record_audit(self, event: WorkspaceAuditEvent) -> None:
        # 审计必须写在同一个事务边界内：另开一条连接会在当前事务持有写锁时触发 database is locked。
        self.conn.execute(_AUDIT_INSERT, _audit_params(event))


_APPLICATION_UPSERT = text(
    "INSERT INTO workspace_applications (application_id, workspace_id, owner_user_id, name, description, "
    "status, created_at, updated_at) "
    "VALUES (:application_id, :workspace_id, :owner_user_id, :name, :description, :status, :created_at, :updated_at) "
    "ON CONFLICT (application_id) DO UPDATE SET name = excluded.name, description = excluded.description, "
    "status = excluded.status, updated_at = excluded.updated_at"
)


def _application_params(application: WorkspaceApplication) -> dict:
    return {
        "application_id": application.application_id,
        "workspace_id": application.workspace_id,
        "owner_user_id": application.owner_user_id,
        "name": application.name,
        "description": application.description,
        "status": application.status.value,
        "created_at": _iso(application.created_at),
        "updated_at": _iso(application.updated_at),
    }


_AUDIT_INSERT = text(
    "INSERT INTO workspace_audit_events (event_id, event_type, workspace_id, actor_user_id, "
    "target_user_id, outcome_code, message, occurred_at) "
    "VALUES (:event_id, :event_type, :workspace_id, :actor_user_id, :target_user_id, "
    ":outcome_code, :message, :occurred_at)"
)


def _audit_params(event: WorkspaceAuditEvent) -> dict:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "workspace_id": event.workspace_id,
        "actor_user_id": event.actor_user_id,
        "target_user_id": event.target_user_id,
        "outcome_code": event.outcome_code,
        "message": event.message,
        "occurred_at": _iso(event.occurred_at),
    }


class SqlWorkspaceRepository:
    def __init__(self, engine, db_path: Path, logger: logging.Logger | None = None) -> None:
        self.engine = engine
        self.db_path = db_path
        self.logger = logger
        run_migrations(db_path, logger)

    @contextmanager
    def unit_of_work(self):
        conn = self.engine.connect()
        try:
            yield SqlUnitOfWork(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM workspaces WHERE workspace_id = :workspace_id"),
                {"workspace_id": workspace_id},
            ).fetchone()
            return self._to_workspace(row) if row else None

    def get_active_membership(self, workspace_id: str, user_id: str) -> WorkspaceMembership | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT * FROM workspace_memberships "
                    "WHERE workspace_id = :workspace_id AND user_id = :user_id AND status = 'active'"
                ),
                {"workspace_id": workspace_id, "user_id": user_id},
            ).fetchone()
            return self._to_membership(row) if row else None

    def list_active_memberships_for_user(self, user_id: str) -> list[WorkspaceMembership]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT * FROM workspace_memberships WHERE user_id = :user_id AND status = 'active' "
                    "ORDER BY joined_at"
                ),
                {"user_id": user_id},
            ).fetchall()
            return [self._to_membership(row) for row in rows]

    def list_active_members(self, workspace_id: str) -> list[WorkspaceMemberView]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT m.user_id, u.username, m.role, m.joined_at FROM workspace_memberships m "
                    "JOIN user_accounts u ON u.user_id = m.user_id "
                    "WHERE m.workspace_id = :workspace_id AND m.status = 'active' ORDER BY m.joined_at"
                ),
                {"workspace_id": workspace_id},
            ).fetchall()
            return [
                WorkspaceMemberView(
                    user_id=row[0],
                    username=row[1],
                    role=row[2],
                    joined_at=_parse(row[3]),
                )
                for row in rows
            ]

    def save_membership(self, membership: WorkspaceMembership) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO workspace_memberships (membership_id, workspace_id, user_id, role, status, joined_at, "
                    "removed_at, created_by_user_id, created_at, updated_at) "
                    "VALUES (:membership_id, :workspace_id, :user_id, :role, :status, :joined_at, :removed_at, "
                    ":created_by_user_id, :created_at, :updated_at) "
                    "ON CONFLICT (membership_id) DO UPDATE SET role = excluded.role, status = excluded.status, "
                    "removed_at = excluded.removed_at, updated_at = excluded.updated_at"
                ),
                {
                    "membership_id": membership.membership_id,
                    "workspace_id": membership.workspace_id,
                    "user_id": membership.user_id,
                    "role": membership.role.value,
                    "status": membership.status.value,
                    "joined_at": _iso(membership.joined_at),
                    "removed_at": _iso(membership.removed_at),
                    "created_by_user_id": membership.created_by_user_id,
                    "created_at": _iso(membership.created_at),
                    "updated_at": _iso(membership.updated_at),
                },
            )

    def get_user_by_id(self, user_id: str) -> UserAccount | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM user_accounts WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).mappings().fetchone()
            return self._to_user(row) if row else None

    def count_active_managers(self, workspace_id: str) -> int:
        with self.engine.connect() as conn:
            return conn.execute(
                text(
                    "SELECT COUNT(*) FROM workspace_memberships "
                    "WHERE workspace_id = :workspace_id AND status = 'active' AND role = 'manager'"
                ),
                {"workspace_id": workspace_id},
            ).fetchone()[0]

    def find_user_by_username(self, username: str) -> UserAccount | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM user_accounts WHERE username = :username"),
                {"username": username},
            ).mappings().fetchone()
            return self._to_user(row) if row else None

    def get_preference(self, user_id: str) -> UserWorkspacePreference | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM user_workspace_preferences WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
            return (
                UserWorkspacePreference(
                    user_id=row[0], last_workspace_id=row[1], updated_at=_parse(row[2])
                )
                if row
                else None
            )

    def save_preference(self, preference: UserWorkspacePreference) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO user_workspace_preferences (user_id, last_workspace_id, updated_at) "
                    "VALUES (:user_id, :last_workspace_id, :updated_at) "
                    "ON CONFLICT (user_id) DO UPDATE SET last_workspace_id = excluded.last_workspace_id, "
                    "updated_at = excluded.updated_at"
                ),
                {
                    "user_id": preference.user_id,
                    "last_workspace_id": preference.last_workspace_id,
                    "updated_at": _iso(preference.updated_at),
                },
            )

    def record_audit(self, event: WorkspaceAuditEvent) -> None:
        # 不在事务内调用（例如认证失败）时只能自己开一条连接；在事务内则走 SqlUnitOfWork.record_audit。
        with self.engine.begin() as conn:
            conn.execute(_AUDIT_INSERT, _audit_params(event))

    def list_applications(self, workspace_id: str) -> list[WorkspaceApplication]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT * FROM workspace_applications WHERE workspace_id = :workspace_id "
                    "ORDER BY updated_at DESC, application_id"
                ),
                {"workspace_id": workspace_id},
            ).mappings().fetchall()
            return [self._to_application(row) for row in rows]

    def get_application(self, application_id: str) -> WorkspaceApplication | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM workspace_applications WHERE application_id = :application_id"),
                {"application_id": application_id},
            ).mappings().fetchone()
            return self._to_application(row) if row else None

    def find_application_by_name(self, workspace_id: str, name: str) -> WorkspaceApplication | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT * FROM workspace_applications "
                    "WHERE workspace_id = :workspace_id AND name = :name"
                ),
                {"workspace_id": workspace_id, "name": name},
            ).mappings().fetchone()
            return self._to_application(row) if row else None

    def save_application(self, application: WorkspaceApplication) -> None:
        with self.engine.begin() as conn:
            conn.execute(_APPLICATION_UPSERT, _application_params(application))

    def _to_application(self, row) -> WorkspaceApplication:
        return WorkspaceApplication(
            application_id=row["application_id"],
            workspace_id=row["workspace_id"],
            owner_user_id=row["owner_user_id"],
            name=row["name"],
            description=row["description"],
            created_at=_parse(row["created_at"]),
            updated_at=_parse(row["updated_at"]),
            status=ApplicationStatus(row["status"]),
        )

    def _to_workspace(self, row) -> Workspace:
        return Workspace(
            workspace_id=row[0],
            name=row[1],
            created_by_user_id=row[2],
            created_at=_parse(row[3]),
            updated_at=_parse(row[4]),
            status=WorkspaceStatus(row[5]),
        )

    def _to_membership(self, row) -> WorkspaceMembership:
        return WorkspaceMembership(
            membership_id=row[0],
            workspace_id=row[1],
            user_id=row[2],
            role=WorkspaceRole(row[3]),
            status=MembershipStatus(row[4]),
            joined_at=_parse(row[5]),
            removed_at=_parse(row[6]),
            created_by_user_id=row[7],
            created_at=_parse(row[8]),
            updated_at=_parse(row[9]),
        )

    def _to_user(self, row) -> UserAccount:
        return UserAccount(
            user_id=row["user_id"],
            email=row["email"],
            username=row["username"],
            password_hash=row["password_hash"],
            password_hash_version=row["password_hash_version"],
            created_at=_parse(row["created_at"]),
            updated_at=_parse(row["updated_at"]),
            email_verified_at=_parse(row["email_verified_at"]),
            password_updated_at=_parse(row["password_updated_at"]),
            last_login_at=_parse(row["last_login_at"]),
        )

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.auth.entities import UserAccount
from src.domain.workspace.entities import (
    UserWorkspacePreference,
    Workspace,
    WorkspaceApplication,
    WorkspaceAuditEvent,
    WorkspaceMembership,
)


@dataclass(frozen=True)
class WorkspaceSummary:
    workspace_id: str
    name: str
    role: str
    is_current: bool


@dataclass(frozen=True)
class WorkspaceMemberView:
    user_id: str
    username: str
    role: str
    joined_at: datetime


class WorkspaceUnitOfWork(Protocol):
    """注册与默认工作空间创建必须原子完成的写入边界。"""

    def save_user(self, user: UserAccount) -> None: ...

    def save_workspace(self, workspace: Workspace) -> None: ...

    def save_membership(self, membership: WorkspaceMembership) -> None: ...

    def save_preference(self, preference: UserWorkspacePreference) -> None: ...

    def save_application(self, application: WorkspaceApplication) -> None: ...

    def record_audit(self, event: WorkspaceAuditEvent) -> None: ...


class WorkspaceRepositoryPort(Protocol):
    def unit_of_work(self) -> AbstractContextManager[WorkspaceUnitOfWork]: ...

    def get_workspace(self, workspace_id: str) -> Workspace | None: ...

    def get_active_membership(self, workspace_id: str, user_id: str) -> WorkspaceMembership | None: ...

    def list_active_memberships_for_user(self, user_id: str) -> list[WorkspaceMembership]: ...

    def list_active_members(self, workspace_id: str) -> list[WorkspaceMemberView]: ...

    def save_membership(self, membership: WorkspaceMembership) -> None: ...

    def get_user_by_id(self, user_id: str) -> UserAccount | None: ...

    def count_active_managers(self, workspace_id: str) -> int: ...

    def find_user_by_username(self, username: str) -> UserAccount | None: ...

    def get_preference(self, user_id: str) -> UserWorkspacePreference | None: ...

    def save_preference(self, preference: UserWorkspacePreference) -> None: ...

    def record_audit(self, event: WorkspaceAuditEvent) -> None: ...

    def list_applications(self, workspace_id: str) -> list[WorkspaceApplication]: ...

    def get_application(self, application_id: str) -> WorkspaceApplication | None: ...

    def find_application_by_name(self, workspace_id: str, name: str) -> WorkspaceApplication | None: ...

    def save_application(self, application: WorkspaceApplication) -> None: ...

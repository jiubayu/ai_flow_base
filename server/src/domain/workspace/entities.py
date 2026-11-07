from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.workspace.value_objects import (
    ApplicationStatus,
    MembershipStatus,
    WorkspaceEventType,
    WorkspaceRole,
    WorkspaceStatus,
    is_valid_application_description,
    is_valid_application_name,
    normalize_application_description,
    normalize_application_name,
)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE


@dataclass
class WorkspaceMembership:
    membership_id: str
    workspace_id: str
    user_id: str
    role: WorkspaceRole
    joined_at: datetime
    created_at: datetime
    status: MembershipStatus = MembershipStatus.ACTIVE
    created_by_user_id: str | None = None
    removed_at: datetime | None = None
    updated_at: datetime | None = None

    def change_role(self, new_role: WorkspaceRole, now: datetime) -> None:
        if self.status is not MembershipStatus.ACTIVE:
            raise ValueError(f"成员关系 {self.membership_id} 已移出，不能变更角色")
        if self.role is new_role:
            raise ValueError(f"成员关系 {self.membership_id} 角色已是 {new_role.value}")
        self.role = new_role
        self.updated_at = now

    def remove(self, now: datetime) -> None:
        if self.status is not MembershipStatus.ACTIVE:
            raise ValueError(f"成员关系 {self.membership_id} 已移出，不能重复移除")
        self.status = MembershipStatus.REMOVED
        self.removed_at = now
        self.updated_at = now


@dataclass
class UserWorkspacePreference:
    user_id: str
    last_workspace_id: str
    updated_at: datetime

    def points_to(self, workspace_id: str) -> bool:
        return self.last_workspace_id == workspace_id


@dataclass
class WorkspaceApplication:
    application_id: str
    workspace_id: str
    owner_user_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    status: ApplicationStatus = ApplicationStatus.DRAFT

    def update_summary(self, name: str, description: str, now: datetime) -> None:
        """按 data-model §4 校验后更新名称与描述；status 不允许用户修改。"""
        if not is_valid_application_name(name):
            raise ValueError(f"应用 {self.application_id} 名称无效：必须为 1-80 个非空白字符")
        if not is_valid_application_description(description):
            raise ValueError(f"应用 {self.application_id} 描述无效：不能超过 500 字符")
        self.name = normalize_application_name(name)
        self.description = normalize_application_description(description)
        self.updated_at = now

    def to_card_view(self) -> "ApplicationCardView":
        return ApplicationCardView(
            application_id=self.application_id,
            name=self.name,
            description=self.description,
            status=self.status.value,
            updated_at=self.updated_at,
        )

    def to_canvas_view(self) -> "ApplicationCanvasView":
        return ApplicationCanvasView(application_id=self.application_id)


@dataclass(frozen=True)
class ApplicationCardView:
    application_id: str
    name: str
    description: str
    status: str
    updated_at: datetime


@dataclass(frozen=True)
class ApplicationCanvasView:
    """005 范围内画布恒为只读空态（spec US3 / data-model §5）。"""

    application_id: str
    mode: str = "empty"
    editable: bool = False
    entry_label: str = "开始编排"


@dataclass
class WorkspaceAuditEvent:
    event_id: str
    event_type: WorkspaceEventType
    outcome_code: str
    message: str
    occurred_at: datetime
    workspace_id: str | None = None
    actor_user_id: str | None = None
    target_user_id: str | None = None

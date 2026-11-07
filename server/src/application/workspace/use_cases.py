from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from src.application.workspace.errors import (
    ApplicationDescriptionInvalidError,
    ApplicationNameDuplicatedError,
    ApplicationNameInvalidError,
    ApplicationNotFoundError,
    UserNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceCreationError,
    WorkspaceCurrentMissingError,
    WorkspaceManagerRequiredError,
    WorkspaceMemberAlreadyExistsError,
    WorkspaceMemberNotFoundError,
    WorkspaceNotFoundError,
    WorkspaceLastManagerProtectedError,
    WorkspaceRoleInvalidError,
)
from src.application.workspace.ports import WorkspaceMemberView, WorkspaceRepositoryPort, WorkspaceSummary
from src.domain.auth.entities import UserAccount
from src.domain.workspace.entities import (
    UserWorkspacePreference,
    Workspace,
    WorkspaceApplication,
    WorkspaceAuditEvent,
    WorkspaceMembership,
)
from src.domain.workspace.services import can_change_role, can_remove, is_active_manager
from src.domain.workspace.value_objects import (
    MembershipStatus,
    WorkspaceEventType,
    WorkspaceRole,
    default_workspace_name,
    is_valid_application_description,
    is_valid_application_name,
    is_valid_role,
    normalize_application_description,
    normalize_application_name,
    normalize_username,
)


@dataclass(frozen=True)
class WorkspaceContextResult:
    current: WorkspaceSummary | None
    available: tuple[WorkspaceSummary, ...]


@dataclass(frozen=True)
class WorkspaceOverviewResult:
    """005：当前默认工作空间 + 其下应用卡片列表（spec US1）。"""

    workspace: Workspace
    applications: tuple[WorkspaceApplication, ...]


class WorkspaceUseCase:
    def __init__(
        self,
        repo: WorkspaceRepositoryPort,
        clock,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repo = repo
        self.clock = clock
        self.logger = logger

    def _audit(
        self,
        event_type: WorkspaceEventType,
        *,
        outcome_code: str,
        message: str,
        workspace_id: str | None = None,
        actor_user_id: str | None = None,
        target_user_id: str | None = None,
        uow=None,
    ) -> None:
        event = WorkspaceAuditEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            outcome_code=outcome_code,
            message=message,
            occurred_at=self.clock.now(),
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
        )
        # 调用方持有事务时审计必须写在同一条连接上，否则 SQLite 会因写锁冲突而 database is locked。
        if uow is not None:
            uow.record_audit(event)
        else:
            self.repo.record_audit(event)
        if self.logger is not None:
            self.logger.debug(f"工作空间审计：{event_type.value} [{outcome_code}] {message}")

    def create_default_workspace(
        self, user: UserAccount, now: datetime, uow
    ) -> tuple[Workspace, WorkspaceMembership]:
        """在调用方的事务边界内创建默认工作空间、管理者成员关系与当前工作空间偏好。"""
        workspace = Workspace(
            workspace_id=str(uuid4()),
            name=default_workspace_name(user.username),
            created_by_user_id=user.user_id,
            created_at=now,
            updated_at=now,
        )
        membership = WorkspaceMembership(
            membership_id=str(uuid4()),
            workspace_id=workspace.workspace_id,
            user_id=user.user_id,
            role=WorkspaceRole.MANAGER,
            status=MembershipStatus.ACTIVE,
            joined_at=now,
            created_at=now,
            updated_at=now,
            created_by_user_id=user.user_id,
        )
        preference = UserWorkspacePreference(
            user_id=user.user_id,
            last_workspace_id=workspace.workspace_id,
            updated_at=now,
        )
        uow.save_workspace(workspace)
        uow.save_membership(membership)
        uow.save_preference(preference)
        self._audit(
            WorkspaceEventType.WORKSPACE_CREATED,
            outcome_code="WORKSPACE_CREATED",
            message=f"为用户 {user.username} 创建默认工作空间 {workspace.name}",
            workspace_id=workspace.workspace_id,
            actor_user_id=user.user_id,
            uow=uow,
        )
        if self.logger is not None:
            self.logger.info(f"默认工作空间创建完成：user={user.user_id} workspace={workspace.workspace_id}")
        return workspace, membership

    def _summaries(self, user_id: str, current_workspace_id: str | None) -> tuple[WorkspaceSummary, ...]:
        memberships = self.repo.list_active_memberships_for_user(user_id)
        summaries: list[WorkspaceSummary] = []
        for membership in memberships:
            workspace = self.repo.get_workspace(membership.workspace_id)
            if workspace is None:
                continue
            summaries.append(
                WorkspaceSummary(
                    workspace_id=workspace.workspace_id,
                    name=workspace.name,
                    role=membership.role.value,
                    is_current=workspace.workspace_id == current_workspace_id,
                )
            )
        return tuple(summaries)

    def resolve_current_workspace(self, user_id: str) -> WorkspaceContextResult:
        """按用户偏好解析当前工作空间；偏好不可访问时回退到任一仍可访问的工作空间。"""
        now = self.clock.now()
        memberships = self.repo.list_active_memberships_for_user(user_id)
        if not memberships:
            return WorkspaceContextResult(current=None, available=())

        preference = self.repo.get_preference(user_id)
        accessible = {membership.workspace_id for membership in memberships}
        current_id = preference.last_workspace_id if preference and preference.last_workspace_id in accessible else None
        if current_id is None:
            current_id = sorted(accessible)[0]
            if preference is not None:
                self.repo.save_preference(
                    UserWorkspacePreference(user_id=user_id, last_workspace_id=current_id, updated_at=now)
                )
                self._audit(
                    WorkspaceEventType.WORKSPACE_SWITCHED,
                    outcome_code="PREFERENCE_FALLBACK",
                    message=f"用户 {user_id} 上次选择的工作空间已不可访问，回退到 {current_id}",
                    workspace_id=current_id,
                    actor_user_id=user_id,
                )

        available = self._summaries(user_id, current_id)
        current = next((item for item in available if item.is_current), None)
        return WorkspaceContextResult(current=current, available=available)

    def list_workspaces(self, user_id: str) -> WorkspaceContextResult:
        return self.resolve_current_workspace(user_id)

    def switch_workspace(self, user_id: str, workspace_id: str) -> WorkspaceContextResult:
        workspace = self.repo.get_workspace(workspace_id)
        if workspace is None:
            self._audit(
                WorkspaceEventType.WORKSPACE_ACCESS_DENIED,
                outcome_code="WORKSPACE_NOT_FOUND",
                message=f"用户 {user_id} 尝试访问不存在的工作空间",
                actor_user_id=user_id,
            )
            raise WorkspaceNotFoundError("工作空间不存在或不可访问")

        membership = self.repo.get_active_membership(workspace_id, user_id)
        if membership is None:
            self._audit(
                WorkspaceEventType.WORKSPACE_ACCESS_DENIED,
                outcome_code="WORKSPACE_ACCESS_DENIED",
                message=f"用户 {user_id} 不是工作空间 {workspace_id} 的成员",
                workspace_id=workspace_id,
                actor_user_id=user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"工作空间越权访问被拒绝：actor={user_id} workspace={workspace_id}")
            raise WorkspaceAccessDeniedError("你不是该工作空间的成员")

        now = self.clock.now()
        self.repo.save_preference(UserWorkspacePreference(user_id=user_id, last_workspace_id=workspace_id, updated_at=now))
        self._audit(
            WorkspaceEventType.WORKSPACE_SWITCHED,
            outcome_code="WORKSPACE_SWITCHED",
            message=f"用户 {user_id} 切换当前工作空间到 {workspace_id}",
            workspace_id=workspace_id,
            actor_user_id=user_id,
        )
        return self.resolve_current_workspace(user_id)

    def _require_current_membership(self, user_id: str) -> WorkspaceMembership:
        context = self.resolve_current_workspace(user_id)
        if context.current is None:
            raise WorkspaceCurrentMissingError("当前没有可用工作空间")
        membership = self.repo.get_active_membership(context.current.workspace_id, user_id)
        if membership is None:
            raise WorkspaceAccessDeniedError("你不是当前工作空间的成员")
        return membership

    def list_members(self, user_id: str) -> list[WorkspaceMemberView]:
        membership = self._require_current_membership(user_id)
        return self.repo.list_active_members(membership.workspace_id)

    def add_member(self, actor_user_id: str, username: str, role: str) -> WorkspaceMemberView:
        membership = self._require_current_membership(actor_user_id)
        if not is_active_manager(membership):
            self._audit(
                WorkspaceEventType.WORKSPACE_ACCESS_DENIED,
                outcome_code="WORKSPACE_MANAGER_REQUIRED",
                message=f"普通成员 {actor_user_id} 尝试添加成员",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"成员管理被拒绝：actor={actor_user_id} workspace={membership.workspace_id} 需要管理者角色")
            raise WorkspaceManagerRequiredError("只有管理者可以添加成员")

        if not is_valid_role(role):
            self._audit(
                WorkspaceEventType.MEMBER_ADDED,
                outcome_code="WORKSPACE_ROLE_INVALID",
                message=f"添加成员时角色无效：{role}",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
            )
            raise WorkspaceRoleInvalidError("角色只能是 manager 或 member")

        target = self.repo.find_user_by_username(normalize_username(username))
        if target is None:
            self._audit(
                WorkspaceEventType.MEMBER_ADDED,
                outcome_code="USER_NOT_FOUND",
                message=f"用户名不存在：{username}",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"添加成员失败：用户名不存在 {username}")
            raise UserNotFoundError("用户名不存在")

        existing = self.repo.get_active_membership(membership.workspace_id, target.user_id)
        if existing is not None:
            self._audit(
                WorkspaceEventType.MEMBER_ADDED,
                outcome_code="MEMBER_ALREADY_EXISTS",
                message=f"用户 {target.username} 已是当前工作空间成员",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
                target_user_id=target.user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"重复成员关系被拒绝：user={target.user_id} workspace={membership.workspace_id}")
            raise WorkspaceMemberAlreadyExistsError("该用户已是当前工作空间成员")

        now = self.clock.now()
        new_membership = WorkspaceMembership(
            membership_id=str(uuid4()),
            workspace_id=membership.workspace_id,
            user_id=target.user_id,
            role=WorkspaceRole(role),
            status=MembershipStatus.ACTIVE,
            joined_at=now,
            created_at=now,
            updated_at=now,
            created_by_user_id=actor_user_id,
        )
        self.repo.save_membership(new_membership)
        self._audit(
            WorkspaceEventType.MEMBER_ADDED,
            outcome_code="MEMBER_ADDED",
            message=f"添加成员 {target.username} 角色 {role}",
            workspace_id=membership.workspace_id,
            actor_user_id=actor_user_id,
            target_user_id=target.user_id,
        )
        if self.logger is not None:
            self.logger.info(
                f"成员添加成功：actor={actor_user_id} target={target.user_id} "
                f"workspace={membership.workspace_id} role={role}"
            )
        return WorkspaceMemberView(
            user_id=target.user_id,
            username=target.username,
            role=role,
            joined_at=now,
        )

    def remove_member(self, actor_user_id: str, target_user_id: str) -> None:
        membership = self._require_current_membership(actor_user_id)
        if not is_active_manager(membership):
            self._audit(
                WorkspaceEventType.WORKSPACE_ACCESS_DENIED,
                outcome_code="WORKSPACE_MANAGER_REQUIRED",
                message=f"普通成员 {actor_user_id} 尝试删除成员",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"成员管理被拒绝：actor={actor_user_id} workspace={membership.workspace_id} 需要管理者角色")
            raise WorkspaceManagerRequiredError("只有管理者可以删除成员")

        target = self.repo.get_active_membership(membership.workspace_id, target_user_id)
        if target is None:
            self._audit(
                WorkspaceEventType.MEMBER_REMOVED,
                outcome_code="WORKSPACE_MEMBER_NOT_FOUND",
                message=f"删除成员失败：目标成员不存在",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
            )
            raise WorkspaceMemberNotFoundError("该用户不是当前工作空间成员")

        if not can_remove(target, self.repo.count_active_managers(membership.workspace_id)):
            self._audit(
                WorkspaceEventType.MEMBER_REMOVED,
                outcome_code="LAST_MANAGER_PROTECTED",
                message=f"拒绝移除最后一个管理者 {target_user_id}",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"最后管理者保护生效：workspace={membership.workspace_id} target={target_user_id}")
            raise WorkspaceLastManagerProtectedError("不能移除工作空间的最后一个管理者")

        target.remove(self.clock.now())
        self.repo.save_membership(target)
        self._audit(
            WorkspaceEventType.MEMBER_REMOVED,
            outcome_code="MEMBER_REMOVED",
            message=f"成员 {target_user_id} 已移出工作空间",
            workspace_id=membership.workspace_id,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
        )
        if self.logger is not None:
            self.logger.info(
                f"成员删除成功：actor={actor_user_id} target={target_user_id} workspace={membership.workspace_id}"
            )

    def change_role(self, actor_user_id: str, target_user_id: str, role: str) -> WorkspaceMemberView:
        membership = self._require_current_membership(actor_user_id)
        if not is_active_manager(membership):
            self._audit(
                WorkspaceEventType.WORKSPACE_ACCESS_DENIED,
                outcome_code="WORKSPACE_MANAGER_REQUIRED",
                message=f"普通成员 {actor_user_id} 尝试变更角色",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"成员管理被拒绝：actor={actor_user_id} workspace={membership.workspace_id} 需要管理者角色")
            raise WorkspaceManagerRequiredError("只有管理者可以变更成员角色")

        if not is_valid_role(role):
            self._audit(
                WorkspaceEventType.MEMBER_ROLE_CHANGED,
                outcome_code="WORKSPACE_ROLE_INVALID",
                message=f"角色变更失败：无效角色 {role}",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
            )
            raise WorkspaceRoleInvalidError("角色只能是 manager 或 member")

        target = self.repo.get_active_membership(membership.workspace_id, target_user_id)
        if target is None:
            self._audit(
                WorkspaceEventType.MEMBER_ROLE_CHANGED,
                outcome_code="WORKSPACE_MEMBER_NOT_FOUND",
                message=f"角色变更失败：目标成员不存在",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
            )
            raise WorkspaceMemberNotFoundError("该用户不是当前工作空间成员")

        if not can_change_role(target, WorkspaceRole(role), self.repo.count_active_managers(membership.workspace_id)):
            self._audit(
                WorkspaceEventType.MEMBER_ROLE_CHANGED,
                outcome_code="LAST_MANAGER_PROTECTED",
                message=f"拒绝将最后一个管理者降级为成员 {target_user_id}",
                workspace_id=membership.workspace_id,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
            )
            if self.logger is not None:
                self.logger.warning(f"最后管理者保护生效：workspace={membership.workspace_id} target={target_user_id}")
            raise WorkspaceLastManagerProtectedError("不能将工作空间的最后一个管理者降级为成员")

        target.change_role(WorkspaceRole(role), self.clock.now())
        self.repo.save_membership(target)
        self._audit(
            WorkspaceEventType.MEMBER_ROLE_CHANGED,
            outcome_code="MEMBER_ROLE_CHANGED",
            message=f"成员 {target_user_id} 角色变更为 {role}",
            workspace_id=membership.workspace_id,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
        )
        if self.logger is not None:
            self.logger.info(
                f"角色变更成功：actor={actor_user_id} target={target_user_id} "
                f"workspace={membership.workspace_id} role={role}"
            )
        user = self.repo.get_user_by_id(target.user_id)
        return WorkspaceMemberView(
            user_id=target.user_id,
            username=user.username if user else target_user_id,
            role=target.role.value,
            joined_at=target.joined_at,
        )

    # ------------------------------------------------------------------
    # 005：默认工作空间概览与应用卡片（spec US1/US2/US3，data-model §3-§5）
    # ------------------------------------------------------------------

    def _ensure_current_workspace(self, user_id: str) -> Workspace:
        """解析当前工作空间；缺失时按 spec FR-001 惰性创建个人默认工作空间。"""
        context = self.resolve_current_workspace(user_id)
        if context.current is not None:
            workspace = self.repo.get_workspace(context.current.workspace_id)
            if workspace is not None:
                return workspace
        user = self.repo.get_user_by_id(user_id)
        if user is None:
            raise WorkspaceCreationError("无法为当前会话初始化默认工作空间")
        try:
            with self.repo.unit_of_work() as uow:
                workspace, _ = self.create_default_workspace(user, self.clock.now(), uow)
        except Exception as exc:
            if self.logger is not None:
                self.logger.error(f"默认工作空间初始化失败：user={user_id} error={exc.__class__.__name__}")
            raise WorkspaceCreationError("默认工作空间初始化失败，请稍后重试") from exc
        return workspace

    def get_workspace_overview(self, user_id: str) -> WorkspaceOverviewResult:
        """工作空间概览：默认工作空间信息 + 应用卡片列表（FR-002/FR-003）。"""
        workspace = self._ensure_current_workspace(user_id)
        applications = self.repo.list_applications(workspace.workspace_id)
        if self.logger is not None:
            self.logger.debug(
                f"工作空间概览读取：user={user_id} workspace={workspace.workspace_id} "
                f"applications={len(applications)}"
            )
        return WorkspaceOverviewResult(workspace=workspace, applications=tuple(applications))

    def _validate_application_summary(self, name: str, description: str) -> tuple[str, str]:
        if not is_valid_application_name(name):
            raise ApplicationNameInvalidError("应用名称必须为 1-80 个非空白字符")
        if not is_valid_application_description(description):
            raise ApplicationDescriptionInvalidError("应用描述不能超过 500 字符")
        return normalize_application_name(name), normalize_application_description(description)

    def _require_owned_application(self, user_id: str, application_id: str) -> WorkspaceApplication:
        application = self.repo.get_application(application_id)
        if application is None or application.owner_user_id != user_id:
            if application is not None and self.logger is not None:
                self.logger.warning(
                    f"应用越权访问被拒绝：actor={user_id} application={application_id} "
                    f"workspace={application.workspace_id}"
                )
            self._audit(
                WorkspaceEventType.WORKSPACE_ACCESS_DENIED,
                outcome_code="APPLICATION_NOT_FOUND",
                message=f"用户 {user_id} 尝试访问应用 {application_id}（不存在或不属于该用户）",
                workspace_id=application.workspace_id if application else None,
                actor_user_id=user_id,
            )
            raise ApplicationNotFoundError("应用不存在或无权访问")
        return application

    def create_application(self, user_id: str, name: str, description: str = "") -> WorkspaceApplication:
        """在当前默认工作空间创建应用（FR-004/FR-005，名称按工作空间唯一）。"""
        clean_name, clean_description = self._validate_application_summary(name, description)
        workspace = self._ensure_current_workspace(user_id)

        existing = self.repo.find_application_by_name(workspace.workspace_id, clean_name)
        if existing is not None:
            self._audit(
                WorkspaceEventType.APPLICATION_CREATED,
                outcome_code="APPLICATION_NAME_DUPLICATED",
                message=f"应用名称重复被拒绝：workspace={workspace.workspace_id}",
                workspace_id=workspace.workspace_id,
                actor_user_id=user_id,
            )
            if self.logger is not None:
                self.logger.debug(
                    f"应用名称重复被拒绝：user={user_id} workspace={workspace.workspace_id}"
                )
            raise ApplicationNameDuplicatedError("应用名称已存在")

        now = self.clock.now()
        application = WorkspaceApplication(
            application_id=str(uuid4()),
            workspace_id=workspace.workspace_id,
            owner_user_id=user_id,
            name=clean_name,
            description=clean_description,
            created_at=now,
            updated_at=now,
        )
        self.repo.save_application(application)
        self._audit(
            WorkspaceEventType.APPLICATION_CREATED,
            outcome_code="APPLICATION_CREATED",
            message=f"在 {workspace.workspace_id} 创建应用 {application.application_id}",
            workspace_id=workspace.workspace_id,
            actor_user_id=user_id,
        )
        if self.logger is not None:
            self.logger.info(
                f"应用创建成功：user={user_id} workspace={workspace.workspace_id} "
                f"application={application.application_id}"
            )
        return application

    def get_application_detail(self, user_id: str, application_id: str) -> WorkspaceApplication:
        """应用详情（FR-010/FR-011）；画布视图由实体恒定为只读空态（US3）。"""
        application = self._require_owned_application(user_id, application_id)
        if self.logger is not None:
            self.logger.debug(
                f"应用详情读取：user={user_id} application={application.application_id}"
            )
        return application

    def update_application_summary(
        self, user_id: str, application_id: str, name: str, description: str
    ) -> WorkspaceApplication:
        """编辑应用名称与描述（FR-006/FR-007/FR-008）；名称冲突返回 409。"""
        clean_name, clean_description = self._validate_application_summary(name, description)
        application = self._require_owned_application(user_id, application_id)

        duplicate = self.repo.find_application_by_name(application.workspace_id, clean_name)
        if duplicate is not None and duplicate.application_id != application.application_id:
            self._audit(
                WorkspaceEventType.APPLICATION_UPDATED,
                outcome_code="APPLICATION_NAME_DUPLICATED",
                message=f"编辑应用 {application.application_id} 时名称重复被拒绝",
                workspace_id=application.workspace_id,
                actor_user_id=user_id,
            )
            if self.logger is not None:
                self.logger.debug(
                    f"应用名称重复被拒绝：user={user_id} application={application.application_id} "
                    f"workspace={application.workspace_id}"
                )
            raise ApplicationNameDuplicatedError("应用名称已存在")

        application.update_summary(clean_name, clean_description, self.clock.now())
        self.repo.save_application(application)
        self._audit(
            WorkspaceEventType.APPLICATION_UPDATED,
            outcome_code="APPLICATION_UPDATED",
            message=f"应用 {application.application_id} 名称/描述已更新",
            workspace_id=application.workspace_id,
            actor_user_id=user_id,
        )
        if self.logger is not None:
            self.logger.info(
                f"应用编辑成功：user={user_id} application={application.application_id}"
            )
        return application

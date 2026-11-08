from __future__ import annotations

import logging
from contextlib import contextmanager

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.application.workspace.errors import WorkspaceMemberAlreadyExistsError
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
    WorkspaceRole,
    WorkspaceStatus,
)
from src.infrastructure.persistence.models import (
    UserAccountModel,
    UserWorkspacePreferenceModel,
    WorkspaceApplicationModel,
    WorkspaceAuditEventModel,
    WorkspaceMembershipModel,
    WorkspaceModel,
)


class PostgresUnitOfWork(WorkspaceUnitOfWork):
    """注册相关写入的原子边界：用户、工作空间、成员关系与偏好必须一起提交或一起回滚。"""

    def __init__(self, session) -> None:
        self._session = session

    def save_user(self, user: UserAccount) -> None:
        self._session.merge(_user_model(user))

    def save_workspace(self, workspace: Workspace) -> None:
        self._session.merge(_workspace_model(workspace))

    def save_membership(self, membership: WorkspaceMembership) -> None:
        self._session.merge(_membership_model(membership))

    def save_preference(self, preference: UserWorkspacePreference) -> None:
        self._session.merge(_preference_model(preference))

    def save_application(self, application: WorkspaceApplication) -> None:
        self._session.merge(_application_model(application))

    def record_audit(self, event: WorkspaceAuditEvent) -> None:
        # 审计必须写在同一个事务边界内：另开一条连接会在当前事务持有写锁时阻塞。
        self._session.add(_audit_model(event))


class PostgresWorkspaceRepository:
    def __init__(self, session_factory, logger: logging.Logger | None = None) -> None:
        self._session_factory = session_factory
        self.logger = logger

    @contextmanager
    def unit_of_work(self):
        with self._session_factory.begin() as session:
            yield PostgresUnitOfWork(session)

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        with self._session_factory() as session:
            record = session.scalar(select(WorkspaceModel).where(WorkspaceModel.workspace_id == workspace_id))
            return self._to_workspace(record) if record else None

    def get_active_membership(self, workspace_id: str, user_id: str) -> WorkspaceMembership | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(WorkspaceMembershipModel)
                .where(
                    WorkspaceMembershipModel.workspace_id == workspace_id,
                    WorkspaceMembershipModel.user_id == user_id,
                    WorkspaceMembershipModel.status == MembershipStatus.ACTIVE.value,
                )
            )
            return self._to_membership(record) if record else None

    def list_active_memberships_for_user(self, user_id: str) -> list[WorkspaceMembership]:
        with self._session_factory() as session:
            records = session.scalars(
                select(WorkspaceMembershipModel)
                .where(
                    WorkspaceMembershipModel.user_id == user_id,
                    WorkspaceMembershipModel.status == MembershipStatus.ACTIVE.value,
                )
                .order_by(WorkspaceMembershipModel.joined_at)
            ).all()
            return [self._to_membership(record) for record in records]

    def list_active_members(self, workspace_id: str) -> list[WorkspaceMemberView]:
        with self._session_factory() as session:
            rows = session.execute(
                select(
                    WorkspaceMembershipModel.user_id,
                    UserAccountModel.username,
                    WorkspaceMembershipModel.role,
                    WorkspaceMembershipModel.joined_at,
                )
                .join(UserAccountModel, UserAccountModel.user_id == WorkspaceMembershipModel.user_id)
                .where(
                    WorkspaceMembershipModel.workspace_id == workspace_id,
                    WorkspaceMembershipModel.status == MembershipStatus.ACTIVE.value,
                )
                .order_by(WorkspaceMembershipModel.joined_at)
            ).all()
            return [
                WorkspaceMemberView(
                    user_id=row[0],
                    username=row[1],
                    role=row[2],
                    joined_at=row[3],
                )
                for row in rows
            ]

    def save_membership(self, membership: WorkspaceMembership) -> None:
        try:
            with self._session_factory.begin() as session:
                session.merge(_membership_model(membership))
        except IntegrityError as exc:
            # 只有唯一索引冲突才是"已是成员"；外键等其他完整性错误原样抛出。
            if getattr(exc.orig, "sqlstate", None) != "23505":
                raise
            raise WorkspaceMemberAlreadyExistsError(
                f"工作空间 {membership.workspace_id} 中用户 {membership.user_id} 已是成员"
            ) from exc

    def get_user_by_id(self, user_id: str) -> UserAccount | None:
        with self._session_factory() as session:
            record = session.get(UserAccountModel, user_id)
            return self._to_user(record) if record else None

    def count_active_managers(self, workspace_id: str) -> int:
        with self._session_factory() as session:
            return session.scalar(
                select(func.count())
                .select_from(WorkspaceMembershipModel)
                .where(
                    WorkspaceMembershipModel.workspace_id == workspace_id,
                    WorkspaceMembershipModel.status == MembershipStatus.ACTIVE.value,
                    WorkspaceMembershipModel.role == WorkspaceRole.MANAGER.value,
                )
            )

    def find_user_by_username(self, username: str) -> UserAccount | None:
        with self._session_factory() as session:
            record = session.scalar(select(UserAccountModel).where(UserAccountModel.username == username))
            return self._to_user(record) if record else None

    def get_preference(self, user_id: str) -> UserWorkspacePreference | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(UserWorkspacePreferenceModel).where(UserWorkspacePreferenceModel.user_id == user_id)
            )
            return (
                UserWorkspacePreference(
                    user_id=record.user_id,
                    last_workspace_id=record.last_workspace_id,
                    updated_at=record.updated_at,
                )
                if record
                else None
            )

    def save_preference(self, preference: UserWorkspacePreference) -> None:
        with self._session_factory.begin() as session:
            session.merge(_preference_model(preference))

    def record_audit(self, event: WorkspaceAuditEvent) -> None:
        # 不在事务内调用（例如认证失败）时只能自己开一条连接；在事务内则走 PostgresUnitOfWork.record_audit。
        with self._session_factory.begin() as session:
            session.add(_audit_model(event))

    def list_applications(self, workspace_id: str) -> list[WorkspaceApplication]:
        with self._session_factory() as session:
            records = session.scalars(
                select(WorkspaceApplicationModel)
                .where(WorkspaceApplicationModel.workspace_id == workspace_id)
                .order_by(WorkspaceApplicationModel.updated_at.desc(), WorkspaceApplicationModel.application_id)
            ).all()
            return [self._to_application(record) for record in records]

    def get_application(self, application_id: str) -> WorkspaceApplication | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(WorkspaceApplicationModel).where(WorkspaceApplicationModel.application_id == application_id)
            )
            return self._to_application(record) if record else None

    def find_application_by_name(self, workspace_id: str, name: str) -> WorkspaceApplication | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(WorkspaceApplicationModel)
                .where(WorkspaceApplicationModel.workspace_id == workspace_id, WorkspaceApplicationModel.name == name)
            )
            return self._to_application(record) if record else None

    def save_application(self, application: WorkspaceApplication) -> None:
        with self._session_factory.begin() as session:
            session.merge(_application_model(application))

    def _to_application(self, record: WorkspaceApplicationModel) -> WorkspaceApplication:
        return WorkspaceApplication(
            application_id=record.application_id,
            workspace_id=record.workspace_id,
            owner_user_id=record.owner_user_id,
            name=record.name,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
            status=ApplicationStatus(record.status),
        )

    def _to_workspace(self, record: WorkspaceModel) -> Workspace:
        return Workspace(
            workspace_id=record.workspace_id,
            name=record.name,
            created_by_user_id=record.created_by_user_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            status=WorkspaceStatus(record.status),
        )

    def _to_membership(self, record: WorkspaceMembershipModel) -> WorkspaceMembership:
        return WorkspaceMembership(
            membership_id=record.membership_id,
            workspace_id=record.workspace_id,
            user_id=record.user_id,
            role=WorkspaceRole(record.role),
            status=MembershipStatus(record.status),
            joined_at=record.joined_at,
            removed_at=record.removed_at,
            created_by_user_id=record.created_by_user_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

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


def _user_model(user: UserAccount) -> UserAccountModel:
    return UserAccountModel(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        email_verified_at=user.email_verified_at,
        password_hash=user.password_hash,
        password_hash_version=user.password_hash_version,
        password_updated_at=user.password_updated_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


def _workspace_model(workspace: Workspace) -> WorkspaceModel:
    return WorkspaceModel(
        workspace_id=workspace.workspace_id,
        name=workspace.name,
        created_by_user_id=workspace.created_by_user_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        status=workspace.status.value,
    )


def _membership_model(membership: WorkspaceMembership) -> WorkspaceMembershipModel:
    return WorkspaceMembershipModel(
        membership_id=membership.membership_id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role.value,
        status=membership.status.value,
        joined_at=membership.joined_at,
        removed_at=membership.removed_at,
        created_by_user_id=membership.created_by_user_id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


def _preference_model(preference: UserWorkspacePreference) -> UserWorkspacePreferenceModel:
    return UserWorkspacePreferenceModel(
        user_id=preference.user_id,
        last_workspace_id=preference.last_workspace_id,
        updated_at=preference.updated_at,
    )


def _application_model(application: WorkspaceApplication) -> WorkspaceApplicationModel:
    return WorkspaceApplicationModel(
        application_id=application.application_id,
        workspace_id=application.workspace_id,
        owner_user_id=application.owner_user_id,
        name=application.name,
        description=application.description,
        status=application.status.value,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _audit_model(event: WorkspaceAuditEvent) -> WorkspaceAuditEventModel:
    return WorkspaceAuditEventModel(
        event_id=event.event_id,
        event_type=event.event_type.value,
        workspace_id=event.workspace_id,
        actor_user_id=event.actor_user_id,
        target_user_id=event.target_user_id,
        outcome_code=event.outcome_code,
        message=event.message,
        occurred_at=event.occurred_at,
    )

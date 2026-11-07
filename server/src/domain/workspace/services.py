from __future__ import annotations

from src.domain.workspace.entities import WorkspaceMembership
from src.domain.workspace.value_objects import MembershipStatus, WorkspaceRole


def is_active_manager(membership: WorkspaceMembership) -> bool:
    return membership.status is MembershipStatus.ACTIVE and membership.role is WorkspaceRole.MANAGER


def can_change_role(
    target: WorkspaceMembership, new_role: WorkspaceRole, active_manager_count: int
) -> bool:
    """最后一个 active 管理者不能被降级为成员。"""
    if target.status is not MembershipStatus.ACTIVE:
        return False
    if target.role is WorkspaceRole.MANAGER and new_role is WorkspaceRole.MEMBER:
        return active_manager_count > 1
    return True


def can_remove(target: WorkspaceMembership, active_manager_count: int) -> bool:
    """最后一个 active 管理者不能被移出工作空间。"""
    if target.status is not MembershipStatus.ACTIVE:
        return False
    if target.role is WorkspaceRole.MANAGER and active_manager_count <= 1:
        return False
    return True

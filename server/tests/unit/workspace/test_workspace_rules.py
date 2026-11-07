"""工作空间领域规则单元测试。"""
from datetime import datetime, timezone

from src.domain.workspace.entities import WorkspaceMembership
from src.domain.workspace.services import can_change_role, can_remove, is_active_manager
from src.domain.workspace.value_objects import (
    MembershipStatus,
    WorkspaceRole,
    default_workspace_name,
    is_valid_role,
    is_valid_username,
    normalize_username,
)


def _membership(role: WorkspaceRole, status: MembershipStatus = MembershipStatus.ACTIVE) -> WorkspaceMembership:
    now = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)
    return WorkspaceMembership(
        membership_id="m1",
        workspace_id="w1",
        user_id="u1",
        role=role,
        status=status,
        joined_at=now,
        created_at=now,
    )


def test_default_workspace_name_uses_username():
    assert default_workspace_name("alice") == "alice 的工作空间"


def test_username_normalized_and_validated():
    assert normalize_username(" Alice ") == "alice"
    assert is_valid_username("alice")
    assert not is_valid_username("ab")
    assert not is_valid_username("a b")


def test_role_values_are_valid():
    assert is_valid_role("manager")
    assert is_valid_role("member")
    assert not is_valid_role("owner")


def test_manager_membership_invariants():
    assert is_active_manager(_membership(WorkspaceRole.MANAGER))
    assert not is_active_manager(_membership(WorkspaceRole.MEMBER))
    assert not is_active_manager(_membership(WorkspaceRole.MANAGER, MembershipStatus.REMOVED))


def test_valid_role_transitions_allowed():
    assert can_change_role(_membership(WorkspaceRole.MEMBER), WorkspaceRole.MANAGER, active_manager_count=1)
    assert can_change_role(_membership(WorkspaceRole.MANAGER), WorkspaceRole.MEMBER, active_manager_count=2)


def test_last_manager_downgrade_protected():
    last_manager = _membership(WorkspaceRole.MANAGER)
    assert not can_change_role(last_manager, WorkspaceRole.MEMBER, active_manager_count=1)
    assert can_change_role(last_manager, WorkspaceRole.MEMBER, active_manager_count=3)


def test_last_manager_removal_protected():
    last_manager = _membership(WorkspaceRole.MANAGER)
    assert not can_remove(last_manager, active_manager_count=1)
    assert can_remove(last_manager, active_manager_count=2)
    assert can_remove(_membership(WorkspaceRole.MEMBER), active_manager_count=1)
    assert not can_remove(_membership(WorkspaceRole.MEMBER, MembershipStatus.REMOVED), active_manager_count=1)

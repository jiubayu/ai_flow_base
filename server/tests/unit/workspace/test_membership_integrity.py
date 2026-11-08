from datetime import datetime, timezone

import pytest

from src.application.workspace.errors import WorkspaceMemberAlreadyExistsError
from src.domain.auth.entities import UserAccount
from src.domain.workspace.entities import Workspace, WorkspaceMembership
from src.domain.workspace.value_objects import WorkspaceRole
from src.infrastructure.persistence.auth_repository import PostgresAuthRepository
from src.infrastructure.persistence.workspace_repository import PostgresWorkspaceRepository

NOW = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)


def _membership(membership_id: str) -> WorkspaceMembership:
    return WorkspaceMembership(
        membership_id=membership_id,
        workspace_id="workspace-1",
        user_id="user-1",
        role=WorkspaceRole.MEMBER,
        joined_at=NOW,
        created_at=NOW,
    )


def test_duplicate_active_membership_raises_domain_error(postgres_session_factory):
    repo = PostgresWorkspaceRepository(postgres_session_factory)
    PostgresAuthRepository(postgres_session_factory).save_user(
        UserAccount(
            user_id="user-1",
            email="membership@example.com",
            username="membership",
            password_hash="hash",
            password_hash_version="scrypt",
            created_at=NOW,
            updated_at=NOW,
            password_updated_at=NOW,
            last_login_at=NOW,
        )
    )
    with repo.unit_of_work() as uow:
        uow.save_workspace(
            Workspace(workspace_id="workspace-1", name="ws", created_by_user_id="user-1", created_at=NOW, updated_at=NOW)
        )
    repo.save_membership(_membership("membership-1"))

    with pytest.raises(WorkspaceMemberAlreadyExistsError):
        repo.save_membership(_membership("membership-2"))

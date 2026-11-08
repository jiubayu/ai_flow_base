"""工作空间集成测试：按用户故事逐步补全。"""
import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src.infrastructure.persistence.models import WorkspaceApplicationModel, WorkspaceModel

PASSWORD = "passw0rd"


def _register(client, fake_sender, email):
    client.post("/api/auth/email-code", json={"email": email})
    code = fake_sender.sent[-1][1]
    return client.post("/api/auth/register", json={"email": email, "code": code, "password": PASSWORD})


def _body_text(response) -> str:
    return json.dumps(response.json())


def _repo(auth_app):
    return auth_app.state.workspace_use_case.repo


def test_register_creates_default_workspace_membership_and_preference(auth_app, auth_client, fake_sender, postgres_session_factory):
    body = _register(auth_client, fake_sender, "alice@example.com").json()
    user_id = body["user"]["user_id"]
    workspace_id = body["workspace"]["current"]["workspace_id"]
    repo = _repo(auth_app)

    workspace = repo.get_workspace(workspace_id)
    assert workspace is not None
    assert workspace.name == "alice 的工作空间"
    assert workspace.created_by_user_id == user_id

    membership = repo.get_active_membership(workspace_id, user_id)
    assert membership is not None
    assert membership.role.value == "manager"
    assert membership.status.value == "active"

    preference = repo.get_preference(user_id)
    assert preference is not None
    assert preference.last_workspace_id == workspace_id

    with postgres_session_factory() as session:
        count = session.scalar(
            select(func.count())
            .select_from(WorkspaceModel)
            .where(WorkspaceModel.created_by_user_id == user_id)
        )
    assert count == 1


def test_preference_persists_and_falls_back_after_membership_removed(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        bob_body = _register(bob, fake_sender, "bob@example.com").json()
        bob_id = bob_body["user"]["user_id"]
        bob_ws = bob_body["workspace"]["current"]["workspace_id"]

        auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
        bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})
        assert _repo(auth_app).get_preference(bob_id).last_workspace_id == alice_ws

        auth_client.delete(f"/api/workspaces/current/members/{bob_id}")
        response = bob.get("/api/workspaces")
        current = response.json()["workspaces"]
        current_ws = next(ws for ws in current if ws["is_current"])
        assert current_ws["workspace_id"] == bob_ws
        assert _repo(auth_app).get_preference(bob_id).last_workspace_id == bob_ws


def test_access_denied_for_non_member_without_data_leak(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        _register(bob, fake_sender, "bob@example.com")
        response = bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})
        assert response.status_code == 403
        detail = response.json()["detail"]
        assert detail["code"] == "WORKSPACE_ACCESS_DENIED"
        assert set(detail) == {"code", "message"}
        assert alice_ws not in _body_text(response)


def test_removed_member_loses_access(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        bob_body = _register(bob, fake_sender, "bob@example.com").json()
        bob_id = bob_body["user"]["user_id"]

        auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
        response = bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})
        assert response.status_code == 200

        auth_client.delete(f"/api/workspaces/current/members/{bob_id}")
        response = bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "WORKSPACE_ACCESS_DENIED"
        # bob 的当前工作空间回退到自己的默认空间，不再包含 alice 空间的成员
        assert [m["username"] for m in bob.get("/api/workspaces/current/members").json()["members"]] == ["bob"]


def test_ordinary_member_cannot_manage_members(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        bob_body = _register(bob, fake_sender, "bob@example.com").json()
        bob_id = bob_body["user"]["user_id"]
        alice_id = _repo(auth_app).find_user_by_username("alice").user_id

        auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
        bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})

        response = bob.post("/api/workspaces/current/members", json={"username": "carol", "role": "member"})
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "WORKSPACE_MANAGER_REQUIRED"

        response = bob.delete(f"/api/workspaces/current/members/{alice_id}")
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "WORKSPACE_MANAGER_REQUIRED"

        response = bob.patch(f"/api/workspaces/current/members/{alice_id}", json={"role": "member"})
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "WORKSPACE_MANAGER_REQUIRED"


def test_same_user_manager_in_one_workspace_member_in_another(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        bob_ws = _register(bob, fake_sender, "bob@example.com").json()["workspace"]["current"]["workspace_id"]
        bob.post("/api/workspaces/current/members", json={"username": "alice", "role": "member"})

        workspaces = auth_client.get("/api/workspaces").json()["workspaces"]
        roles = {ws["workspace_id"]: ws["role"] for ws in workspaces}
        assert roles[alice_ws] == "manager"
        assert roles[bob_ws] == "member"


# ----------------------------------------------------------------------
# 005：应用创建 → 概览 → 编辑 → 隔离 的端到端流程
# ----------------------------------------------------------------------


def test_application_lifecycle_flow(auth_app, auth_client, fake_sender, postgres_session_factory):
    alice_id = _register(auth_client, fake_sender, "alice@example.com").json()["user"]["user_id"]
    repo = _repo(auth_app)

    overview = auth_client.get("/api/workspace/current").json()
    alice_ws = overview["workspace"]["workspace_id"]
    assert overview["applications"] == []

    created = auth_client.post(
        "/api/workspace/applications", json={"name": "客服助手", "description": "处理工单"}
    ).json()["application"]
    application_id = created["application_id"]

    persisted = repo.get_application(application_id)
    assert persisted is not None
    assert persisted.workspace_id == alice_ws
    assert persisted.owner_user_id == alice_id
    assert persisted.status.value == "draft"

    overview = auth_client.get("/api/workspace/current").json()
    assert [a["application_id"] for a in overview["applications"]] == [application_id]

    updated = auth_client.patch(
        f"/api/workspace/applications/{application_id}",
        json={"name": "客服助手 Pro", "description": ""},
    ).json()["application"]
    assert updated["name"] == "客服助手 Pro"
    assert updated["description"] == ""
    detail = auth_client.get(f"/api/workspace/applications/{application_id}").json()["application"]
    assert detail == updated

    with postgres_session_factory() as session:
        row = session.execute(
            select(
                WorkspaceApplicationModel.name,
                WorkspaceApplicationModel.description,
                WorkspaceApplicationModel.status,
            ).where(WorkspaceApplicationModel.application_id == application_id)
        ).fetchone()
    assert row == ("客服助手 Pro", "", "draft")


def test_application_name_unique_per_workspace_only(auth_app, auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    auth_client.post("/api/workspace/applications", json={"name": "同名应用"})
    with TestClient(auth_app) as bob:
        _register(bob, fake_sender, "bob@example.com")
        response = bob.post("/api/workspace/applications", json={"name": "同名应用"})
        assert response.status_code == 201
        response = bob.post("/api/workspace/applications", json={"name": "同名应用"})
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "APPLICATION_NAME_DUPLICATED"


def test_application_isolation_between_users(auth_app, auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    created = auth_client.post("/api/workspace/applications", json={"name": "私密助手"}).json()["application"]
    with TestClient(auth_app) as bob:
        _register(bob, fake_sender, "bob@example.com")
        response = bob.get(f"/api/workspace/applications/{created['application_id']}")
        assert response.status_code == 404
        body_text = _body_text(response)
        assert "私密助手" not in body_text
        assert created["application_id"] not in json.loads(body_text)["detail"]["message"]
        overview = bob.get("/api/workspace/current").json()
        assert overview["applications"] == []



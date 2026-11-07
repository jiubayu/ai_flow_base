"""工作空间 API 契约测试：按用户故事逐步补全。"""
from fastapi.testclient import TestClient

PASSWORD = "passw0rd"


def _register(client, fake_sender, email):
    client.post("/api/auth/email-code", json={"email": email})
    code = fake_sender.sent[-1][1]
    return client.post("/api/auth/register", json={"email": email, "code": code, "password": PASSWORD})


def test_list_workspaces_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.get("/api/workspaces")
    assert response.status_code == 200
    workspaces = response.json()["workspaces"]
    assert len(workspaces) == 1
    workspace = workspaces[0]
    assert workspace["name"] == "alice 的工作空间"
    assert workspace["role"] == "manager"
    assert workspace["is_current"] is True
    assert set(workspace) == {"workspace_id", "name", "role", "is_current"}


def test_switch_workspace_contract(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        _register(bob, fake_sender, "bob@example.com")
        auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
        response = bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})
        assert response.status_code == 200
        body = response.json()
        current = body["current"]
        assert current["workspace_id"] == alice_ws
        assert current["role"] == "member"
        assert current["is_current"] is True
        assert len(body["available"]) == 2


def test_list_members_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.get("/api/workspaces/current/members")
    assert response.status_code == 200
    members = response.json()["members"]
    assert len(members) == 1
    member = members[0]
    assert member["username"] == "alice"
    assert member["role"] == "manager"
    assert set(member) == {"user_id", "username", "role", "joined_at"}


def test_add_member_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "USER_NOT_FOUND"

    bob_id = _register(TestClient(auth_client.app), fake_sender, "bob@example.com").json()["user"]["user_id"]
    response = auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
    assert response.status_code == 201
    member = response.json()["member"]
    assert member["user_id"] == bob_id
    assert member["username"] == "bob"
    assert member["role"] == "member"


def test_add_duplicate_member_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    _register(TestClient(auth_client.app), fake_sender, "bob@example.com")
    auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
    response = auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "WORKSPACE_MEMBER_ALREADY_EXISTS"


def test_add_member_requires_manager_contract(auth_app, auth_client, fake_sender):
    alice_ws = _register(auth_client, fake_sender, "alice@example.com").json()["workspace"]["current"]["workspace_id"]
    with TestClient(auth_app) as bob:
        _register(bob, fake_sender, "bob@example.com")
        auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
        bob.post("/api/workspaces/current", json={"workspace_id": alice_ws})
        response = bob.post("/api/workspaces/current/members", json={"username": "carol", "role": "member"})
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "WORKSPACE_MANAGER_REQUIRED"


def test_remove_member_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    bob_id = _register(TestClient(auth_client.app), fake_sender, "bob@example.com").json()["user"]["user_id"]
    auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
    response = auth_client.delete(f"/api/workspaces/current/members/{bob_id}")
    assert response.status_code == 204
    members = auth_client.get("/api/workspaces/current/members").json()["members"]
    assert [m["username"] for m in members] == ["alice"]


def test_change_role_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    bob_id = _register(TestClient(auth_client.app), fake_sender, "bob@example.com").json()["user"]["user_id"]
    auth_client.post("/api/workspaces/current/members", json={"username": "bob", "role": "member"})
    response = auth_client.patch(f"/api/workspaces/current/members/{bob_id}", json={"role": "manager"})
    assert response.status_code == 200
    assert response.json()["member"]["role"] == "manager"


def test_change_role_invalid_role_contract(auth_client, fake_sender):
    user_id = _register(auth_client, fake_sender, "alice@example.com").json()["user"]["user_id"]
    response = auth_client.patch(f"/api/workspaces/current/members/{user_id}", json={"role": "owner"})
    assert response.status_code == 422


def test_change_role_member_not_found_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    bob_id = _register(TestClient(auth_client.app), fake_sender, "bob@example.com").json()["user"]["user_id"]
    response = auth_client.patch(f"/api/workspaces/current/members/{bob_id}", json={"role": "member"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WORKSPACE_MEMBER_NOT_FOUND"


def test_change_role_last_manager_protected_contract(auth_client, fake_sender):
    alice_id = _register(auth_client, fake_sender, "alice@example.com").json()["user"]["user_id"]
    response = auth_client.patch(f"/api/workspaces/current/members/{alice_id}", json={"role": "member"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "WORKSPACE_LAST_MANAGER_PROTECTED"


def test_remove_last_manager_protected_contract(auth_client, fake_sender):
    alice_id = _register(auth_client, fake_sender, "alice@example.com").json()["user"]["user_id"]
    response = auth_client.delete(f"/api/workspaces/current/members/{alice_id}")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "WORKSPACE_LAST_MANAGER_PROTECTED"


def test_workspace_requires_login_contract(auth_client):
    response = auth_client.get("/api/workspaces")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_SESSION_MISSING"


# ----------------------------------------------------------------------
# 005：/api/workspace 概览与应用契约（contracts/workspace-api.openapi.yaml）
# ----------------------------------------------------------------------

CARD_KEYS = {"application_id", "name", "description", "status", "updated_at"}
DETAIL_KEYS = CARD_KEYS | {"created_at"}


def test_current_workspace_overview_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.get("/api/workspace/current")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"workspace", "applications"}
    workspace = body["workspace"]
    assert workspace["name"] == "alice 的工作空间"
    assert workspace["is_default"] is True
    assert set(workspace) == {"workspace_id", "name", "is_default", "created_at", "updated_at"}
    assert body["applications"] == []


def test_create_application_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.post(
        "/api/workspace/applications", json={"name": " 客服助手 ", "description": " 处理工单 "}
    )
    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"application", "canvas"}
    application = body["application"]
    assert set(application) == DETAIL_KEYS
    assert application["name"] == "客服助手"
    assert application["description"] == "处理工单"
    assert application["status"] == "draft"
    canvas = body["canvas"]
    assert canvas == {"mode": "empty", "editable": False, "entry_label": "开始编排"}


def test_create_application_blank_name_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.post("/api/workspace/applications", json={"name": "   ", "description": ""})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "APPLICATION_NAME_INVALID"


def test_create_application_overlong_description_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.post(
        "/api/workspace/applications", json={"name": "助手", "description": "d" * 501}
    )
    assert response.status_code == 422


def test_create_application_duplicate_name_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    auth_client.post("/api/workspace/applications", json={"name": "报表助手", "description": ""})
    response = auth_client.post("/api/workspace/applications", json={"name": " 报表助手 ", "description": "另一个"})
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "APPLICATION_NAME_DUPLICATED"
    assert set(detail) == {"code", "message"}


def test_get_application_detail_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    created = auth_client.post("/api/workspace/applications", json={"name": "翻译助手"}).json()["application"]
    response = auth_client.get(f"/api/workspace/applications/{created['application_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["application"] == created
    assert body["canvas"] == {"mode": "empty", "editable": False, "entry_label": "开始编排"}


def test_get_application_not_found_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    response = auth_client.get("/api/workspace/applications/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "APPLICATION_NOT_FOUND"


def test_application_cross_user_isolation_contract(auth_app, auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    created = auth_client.post("/api/workspace/applications", json={"name": "私密助手"}).json()["application"]
    with TestClient(auth_app) as bob:
        _register(bob, fake_sender, "bob@example.com")
        response = bob.get(f"/api/workspace/applications/{created['application_id']}")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "APPLICATION_NOT_FOUND"
        response = bob.patch(
            f"/api/workspace/applications/{created['application_id']}",
            json={"name": "被改名", "description": ""},
        )
        assert response.status_code == 404
        overview = bob.get("/api/workspace/current").json()
        assert overview["applications"] == []


def test_update_application_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    created = auth_client.post(
        "/api/workspace/applications", json={"name": "旧名称", "description": "旧描述"}
    ).json()["application"]
    response = auth_client.patch(
        f"/api/workspace/applications/{created['application_id']}",
        json={"name": " 新名称 ", "description": "新描述"},
    )
    assert response.status_code == 200
    application = response.json()["application"]
    assert application["name"] == "新名称"
    assert application["description"] == "新描述"
    assert application["created_at"] == created["created_at"]


def test_update_application_duplicate_name_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    auth_client.post("/api/workspace/applications", json={"name": "助手A"})
    b = auth_client.post("/api/workspace/applications", json={"name": "助手B"}).json()["application"]
    response = auth_client.patch(
        f"/api/workspace/applications/{b['application_id']}", json={"name": "助手A", "description": ""}
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "APPLICATION_NAME_DUPLICATED"


def test_update_application_keeps_own_name_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender, "alice@example.com")
    created = auth_client.post("/api/workspace/applications", json={"name": "助手A"}).json()["application"]
    response = auth_client.patch(
        f"/api/workspace/applications/{created['application_id']}",
        json={"name": "助手A", "description": "只改描述"},
    )
    assert response.status_code == 200
    assert response.json()["application"]["description"] == "只改描述"


def test_workspace_apps_require_login_contract(auth_client):
    assert auth_client.get("/api/workspace/current").status_code == 401
    response = auth_client.get("/api/workspace/current")
    assert response.json()["detail"]["code"] == "AUTH_SESSION_MISSING"
    response = auth_client.post("/api/workspace/applications", json={"name": "x"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_SESSION_MISSING"

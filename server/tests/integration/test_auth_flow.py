from fastapi.testclient import TestClient

PASSWORD = "passw0rd"


def _send_code(client, email):
    return client.post("/api/auth/email-code", json={"email": email})


def _last_code(fake_sender):
    return fake_sender.sent[-1][1]


def test_register_flow(auth_client, fake_sender, fake_clock):
    email = "flow@example.com"
    assert _send_code(auth_client, email).status_code == 202

    limited = _send_code(auth_client, email)
    assert limited.status_code == 429
    assert limited.json()["detail"]["retry_after_seconds"] > 0

    wrong = auth_client.post("/api/auth/register", json={"email": email, "code": "111111", "password": PASSWORD})
    assert wrong.status_code == 400

    registered = auth_client.post(
        "/api/auth/register", json={"email": email, "code": _last_code(fake_sender), "password": PASSWORD}
    )
    assert registered.status_code == 201

    # 注册成功后自动登录：无需再手工登录即可读取当前会话
    session = auth_client.get("/api/auth/session")
    assert session.status_code == 200
    assert session.json()["user"]["email"] == email


def test_rate_limit_window(auth_client, fake_sender, fake_clock):
    email = "window@example.com"
    for i in range(5):
        if i > 0:
            fake_clock.advance(61)
        assert _send_code(auth_client, email).status_code == 202
    assert len(fake_sender.sent) == 5

    blocked = _send_code(auth_client, email)
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["retry_after_seconds"] > 0


def test_login_and_session_restore(auth_app, fake_sender, fake_clock):
    email = "restore@example.com"
    with TestClient(auth_app) as browser_a:
        _send_code(browser_a, email)
        assert browser_a.post(
            "/api/auth/register", json={"email": email, "code": _last_code(fake_sender), "password": PASSWORD}
        ).status_code == 201

        # 刷新页面后仍识别当前登录用户
        assert browser_a.get("/api/auth/session").status_code == 200

        # 另一个浏览器没有会话
        with TestClient(auth_app) as browser_b:
            assert browser_b.get("/api/auth/session").status_code == 401

        # 错误凭证不能登录
        assert browser_b.post("/api/auth/login", json={"email": email, "password": "wrongpass1"}).status_code == 401
        assert browser_a.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_refresh_after_access_expiry(auth_client, fake_sender, fake_clock):
    email = "refresh@example.com"
    _send_code(auth_client, email)
    registered = auth_client.post(
        "/api/auth/register", json={"email": email, "code": _last_code(fake_sender), "password": PASSWORD}
    )
    assert registered.status_code == 201

    # access 过期后无法直接访问受保护接口
    fake_clock.advance(61)
    assert auth_client.get("/api/auth/session").status_code == 401

    # 通过刷新资格恢复当前浏览器会话
    refreshed = auth_client.post("/api/auth/refresh")
    assert refreshed.status_code == 200
    assert auth_client.get("/api/auth/session").status_code == 200

    # 旧刷新资格不可再次使用
    old_grant = _set_cookie_value(registered, "refresh_grant")
    assert auth_client.post("/api/auth/refresh", headers={"Cookie": f"refresh_grant={old_grant}"}).status_code == 401


def test_logout_only_current_browser(auth_app, fake_sender, fake_clock):
    email = "logout@example.com"
    with TestClient(auth_app) as browser_a, TestClient(auth_app) as browser_b:
        _send_code(browser_a, email)
        assert browser_a.post(
            "/api/auth/register", json={"email": email, "code": _last_code(fake_sender), "password": PASSWORD}
        ).status_code == 201
        assert browser_b.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200

        assert browser_a.post("/api/auth/logout").status_code == 204

        # 当前浏览器立即失效，且不会被恢复为已登录
        assert browser_a.get("/api/auth/session").status_code == 401
        assert browser_a.post("/api/auth/refresh").status_code == 401

        # 其他浏览器的会话保持不变
        assert browser_b.get("/api/auth/session").status_code == 200


def _set_cookie_value(response, name):
    for header in response.headers.get_list("set-cookie"):
        cookie_name, _, rest = header.partition("=")
        if cookie_name == name:
            value, _, _ = rest.partition(";")
            return value
    return None

def _set_cookies(response) -> dict:
    values = {}
    for header in response.headers.get_list("set-cookie"):
        name, _, rest = header.partition("=")
        value, _, _ = rest.partition(";")
        values[name] = value
    return values


def _register(client, fake_sender, email="user@example.com", password="passw0rd"):
    client.post("/api/auth/email-code", json={"email": email})
    code = fake_sender.sent[-1][1]
    return client.post("/api/auth/register", json={"email": email, "code": code, "password": password})


def test_send_email_code_contract(auth_client, fake_sender):
    response = auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["retry_after_seconds"] == 60
    assert body["expires_in_seconds"] == 600
    assert fake_sender.sent == [("user@example.com", fake_sender.sent[0][1], 600)]


def test_send_email_code_invalid_email_contract(auth_client):
    response = auth_client.post("/api/auth/email-code", json={"email": "not-an-email"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "email"


def test_send_email_code_already_registered_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender)
    response = auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "email_already_registered"


def test_send_email_code_rate_limited_contract(auth_client, fake_sender, fake_clock):
    auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    response = auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    assert response.status_code == 429
    detail = response.json()["detail"]
    assert detail["code"] == "rate_limited"
    assert detail["retry_after_seconds"] > 0
    fake_clock.advance(61)
    response = auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    assert response.status_code == 202


def test_register_contract(auth_client, fake_sender):
    response = _register(auth_client, fake_sender)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["email_verified"] is True
    assert body["session"]["authenticated"] is True
    cookies = _set_cookies(response)
    assert cookies["access_session"] and cookies["refresh_grant"]
    for header in response.headers.get_list("set-cookie"):
        assert "HttpOnly" in header
    workspace = body["workspace"]
    assert workspace["current"]["name"] == "user 的工作空间"
    assert workspace["current"]["role"] == "manager"
    assert workspace["current"]["is_current"] is True
    assert len(workspace["available"]) == 1


def test_register_invalid_code_contract(auth_client, fake_sender):
    auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    response = auth_client.post(
        "/api/auth/register", json={"email": "user@example.com", "code": "000000", "password": "passw0rd"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_code"


def test_register_password_policy_contract(auth_client, fake_sender):
    auth_client.post("/api/auth/email-code", json={"email": "user@example.com"})
    code = fake_sender.sent[-1][1]
    response = auth_client.post(
        "/api/auth/register", json={"email": "user@example.com", "code": code, "password": "12345678"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "password_policy"


def test_login_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender)
    auth_client.post("/api/auth/logout")
    response = auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "passw0rd"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["session"]["authenticated"] is True
    assert _set_cookies(response)["access_session"]
    assert body["workspace"]["current"]["name"] == "user 的工作空间"


def test_login_invalid_credentials_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender)
    auth_client.post("/api/auth/logout")
    response = auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrongpass1"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "unauthorized"


def test_session_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender)
    response = auth_client.get("/api/auth/session")
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["workspace"]["current"]["is_current"] is True
    assert body["workspace"]["current"]["role"] == "manager"


def test_session_without_cookie_contract(auth_app):
    from fastapi.testclient import TestClient

    with TestClient(auth_app) as fresh:
        response = fresh.get("/api/auth/session")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "unauthorized"


def test_refresh_contract(auth_client, fake_sender, fake_clock):
    register_response = _register(auth_client, fake_sender)
    old_grant = _set_cookies(register_response)["refresh_grant"]
    fake_clock.advance(120)
    response = auth_client.post("/api/auth/refresh")
    assert response.status_code == 200
    new_grant = _set_cookies(response)["refresh_grant"]
    assert new_grant != old_grant
    reuse = auth_client.post("/api/auth/refresh", headers={"Cookie": f"refresh_grant={old_grant}"})
    assert reuse.status_code == 401
    assert reuse.json()["detail"]["code"] == "unauthorized"


def test_logout_contract(auth_client, fake_sender):
    _register(auth_client, fake_sender)
    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 204
    for header in response.headers.get_list("set-cookie"):
        assert "Max-Age=0" in header
    assert auth_client.get("/api/auth/session").status_code == 401

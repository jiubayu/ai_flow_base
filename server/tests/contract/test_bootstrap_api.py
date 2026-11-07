def test_health_contract(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "backend"
    assert "timestamp" in body


def test_submit_demo_task_contract(client, dispatch_calls):
    response = client.post("/api/dev/tasks/demo", json={"message": "bootstrap smoke"})
    assert response.status_code == 202
    body = response.json()
    assert body["state"] == "PENDING"
    assert body["message"] == "bootstrap smoke"
    assert dispatch_calls == [(body["task_id"], "bootstrap smoke")]


def test_get_demo_task_status_contract(client):
    accepted = client.post("/api/dev/tasks/demo", json={"message": "hello"}).json()
    response = client.get(f"/api/dev/tasks/{accepted['task_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == accepted["task_id"]
    assert body["state"] == "PENDING"


def test_task_not_found_contract(client):
    response = client.get("/api/dev/tasks/missing")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "task_not_found"


def test_invalid_request_contract(client):
    response = client.post("/api/dev/tasks/demo", json={"message": ""})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "message"

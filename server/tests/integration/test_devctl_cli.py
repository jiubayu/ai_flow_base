def test_start_status_stop_lifecycle(devctl):
    start = devctl.run("start")
    assert start.returncode == 0, start.stderr
    assert "探针通过" in start.stdout
    assert "进程存活" in start.stdout
    assert str(devctl.root / "server" / "logs") in start.stdout

    status = devctl.run("status")
    assert status.returncode == 0
    assert "state=running" in status.stdout

    stop = devctl.run("stop")
    assert stop.returncode == 0
    assert "已停止" in stop.stdout

    status = devctl.run("status")
    assert "state=running" not in status.stdout
    assert status.stdout.count("state=stopped") == 3


def test_status_reports_stale_pid(devctl):
    pid_path = devctl.root / "server" / ".runtime"
    pid_path.mkdir(parents=True, exist_ok=True)
    (pid_path / "backend.pid").write_text("999999")

    status = devctl.run("status")
    assert "service=backend state=failed" in status.stdout
    assert "已失效" in status.stdout

    stop = devctl.run("stop")
    assert "执行清理" in stop.stdout
    assert not (pid_path / "backend.pid").exists()
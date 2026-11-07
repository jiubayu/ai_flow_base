import socket


def test_missing_config_fails_explicitly(devctl):
    (devctl.root / "server" / ".env").unlink()
    result = devctl.run("start")
    assert result.returncode != 0
    assert "配置文件缺失" in result.stderr


def test_port_conflict_names_responsible_service(devctl):
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", devctl.backend_port))
    try:
        result = devctl.run("start")
        assert result.returncode != 0
        assert "端口冲突" in result.stderr
        assert "backend" in result.stderr
        assert "backend.log" in result.stderr
    finally:
        blocker.close()


def test_repeat_execution_is_rejected(devctl):
    start = devctl.run("start")
    assert start.returncode == 0, start.stderr
    repeat = devctl.run("start")
    assert repeat.returncode != 0
    assert "已在运行" in repeat.stderr
import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, List, Tuple
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from src.core.config import load_config
from src.infrastructure.persistence.database import create_session_factory
from src.infrastructure.persistence.postgres_migrations import initialize_postgres_schema
from src.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
DEVCTL_SCRIPT = REPO_ROOT / "scripts" / "devctl.sh"

FAKE_SERVER_SOURCE = (
    "import http.server, sys\n"
    "class H(http.server.BaseHTTPRequestHandler):\n"
    "    def do_GET(self):\n"
    "        self.send_response(200)\n"
    "        self.send_header('Content-Type', 'application/json')\n"
    "        self.end_headers()\n"
    "        self.wfile.write(b'{\"status\":\"ok\"}')\n"
    "    def log_message(self, *a): pass\n"
    "http.server.HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()\n"
)


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@dataclass
class DevctlHarness:
    root: Path
    backend_port: int
    frontend_port: int

    def write_env(self) -> None:
        env = self.root / "server" / ".env"
        env.write_text(
            "BACKEND_HOST=127.0.0.1\n"
            f"BACKEND_PORT={self.backend_port}\n"
            "LOG_DIR=logs\n"
            "RUNTIME_DIR=.runtime\n"
            "CELERY_BROKER_URL=filesystem://\n"
            "CELERY_BROKER_DIR=.runtime/celery-queue\n"
            "CELERY_RESULT_DB_PATH=.runtime/celery_results.db\n"
            f"FRONTEND_PORT={self.frontend_port}\n"
        )

    def run(self, subcommand: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PATH"] = f"{self.root / 'bin'}:{env['PATH']}"
        env["FAKE_SERVER"] = str(self.root / "fake_server.py")
        return subprocess.run(
            ["bash", str(self.root / "scripts" / "devctl.sh"), subcommand],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )


@pytest.fixture
def devctl(tmp_path: Path) -> DevctlHarness:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "server").mkdir()
    (tmp_path / "ui").mkdir()
    (tmp_path / "bin").mkdir()
    shutil.copy(DEVCTL_SCRIPT, tmp_path / "scripts" / "devctl.sh")
    (tmp_path / "fake_server.py").write_text(FAKE_SERVER_SOURCE)

    backend_port = free_port()
    frontend_port = free_port()

    uv = tmp_path / "bin" / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        'if echo "$*" | grep -q celery; then exec sleep 30; fi\n'
        "port=$(echo \"$*\" | sed -n 's/.*--port \\([0-9]*\\).*/\\1/p')\n"
        f'exec python3 "{tmp_path / "fake_server.py"}" "$port"\n'
    )
    pnpm = tmp_path / "bin" / "pnpm"
    pnpm.write_text(f"#!/bin/sh\nexec python3 \"{tmp_path / 'fake_server.py'}\" {frontend_port}\n")
    uv.chmod(0o755)
    pnpm.chmod(0o755)

    harness = DevctlHarness(root=tmp_path, backend_port=backend_port, frontend_port=frontend_port)
    harness.write_env()
    yield harness
    harness.run("stop")


@pytest.fixture
def config(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "BACKEND_HOST=127.0.0.1\n"
        "BACKEND_PORT=8000\n"
        "LOG_DIR=logs\n"
        "RUNTIME_DIR=.runtime\n"
        "CELERY_BROKER_URL=filesystem://\n"
        "CELERY_BROKER_DIR=.runtime/celery-queue\n"
        "CELERY_RESULT_DB_PATH=results.db\n"
        "DEBUG=true\n"
    )
    return load_config(env)


@pytest.fixture
def dispatch_calls() -> List[Tuple[str, str]]:
    return []


@pytest.fixture
def app(config, dispatch_calls):
    dispatch: Callable[[str, str], None] = lambda task_id, message: dispatch_calls.append((task_id, message))
    return create_app(config, dispatch)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: int) -> None:
        self._now = self._now + timedelta(seconds=seconds)


class RecordingSender:
    """可替换的邮件发送依赖：记录发送内容，不真实外发。"""

    def __init__(self) -> None:
        self.sent: List[Tuple[str, str, int]] = []

    def send(self, to: str, code: str, expires_in_seconds: int) -> None:
        self.sent.append((to, code, expires_in_seconds))


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock(datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def fake_sender() -> RecordingSender:
    return RecordingSender()


@pytest.fixture
def auth_config(tmp_path: Path):
    env = tmp_path / "auth.env"
    env.write_text(
        "BACKEND_HOST=127.0.0.1\n"
        "BACKEND_PORT=8000\n"
        "LOG_DIR=logs\n"
        "RUNTIME_DIR=.runtime\n"
        "CELERY_BROKER_URL=filesystem://\n"
        "CELERY_BROKER_DIR=.runtime/celery-queue\n"
        "CELERY_RESULT_DB_PATH=auth-tests.db\n"
        "DEBUG=true\n"
        "AUTH_ACCESS_TTL_MINUTES=1\n"
        "AUTH_REFRESH_TTL_DAYS=14\n"
        "AUTH_CODE_TTL_MINUTES=10\n"
        "AUTH_CODE_MIN_INTERVAL_SECONDS=60\n"
        "AUTH_CODE_WINDOW_SECONDS=900\n"
        "AUTH_CODE_WINDOW_LIMIT=5\n"
        "AUTH_COOKIE_SECURE=false\n"
    )
    return load_config(env)


@pytest.fixture
def auth_app(auth_config, fake_sender, fake_clock):
    return create_app(auth_config, lambda task_id, message: None, auth_sender=fake_sender, clock=fake_clock)


@pytest.fixture
def auth_client(auth_app):
    with TestClient(auth_app) as c:
        yield c


@pytest.fixture
def postgres_base_database_url() -> str:
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://ai_flow:ai_flow@127.0.0.1:5432/ai_flow_test",
    )


@pytest.fixture
def postgres_database_url(postgres_base_database_url: str, monkeypatch: pytest.MonkeyPatch) -> str:
    schema = f"test_{uuid4().hex}"
    url = make_url(postgres_base_database_url).update_query_dict(
        {"options": f"-csearch_path={schema},public"}
    )
    rendered_url = url.render_as_string(hide_password=False)
    monkeypatch.setenv("DATABASE_URL", rendered_url)
    return rendered_url


@pytest.fixture
def postgres_engine(postgres_base_database_url: str, postgres_database_url: str):
    admin_engine = create_engine(postgres_base_database_url, pool_pre_ping=True)
    schema = make_url(postgres_database_url).query["options"].removeprefix("-csearch_path=").split(",", 1)[0]
    with admin_engine.begin() as connection:
        connection.execute(CreateSchema(schema))
    engine = create_engine(postgres_database_url, pool_pre_ping=True)
    initialize_postgres_schema(engine)
    try:
        yield engine
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        admin_engine.dispose()


@pytest.fixture
def postgres_session_factory(postgres_engine):
    return create_session_factory(postgres_engine)

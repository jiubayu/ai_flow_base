import pytest
from fastapi.testclient import TestClient

from src.core.config import load_config
from src.main import create_app


def test_startup_fails_when_database_unreachable(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "BACKEND_HOST=127.0.0.1\n"
        "BACKEND_PORT=8000\n"
        "LOG_DIR=logs\n"
        "RUNTIME_DIR=.runtime\n"
        "CELERY_BROKER_URL=filesystem://\n"
        "CELERY_BROKER_DIR=.runtime/celery-queue\n"
        "DATABASE_URL=postgresql+psycopg://broken:broken@127.0.0.1:59999/broken\n"
    )
    config = load_config(env)
    app = create_app(config, lambda task_id, message: None)

    with pytest.raises(Exception):
        with TestClient(app):
            pass

    log_text = (config.log_dir / "backend.log").read_text()
    assert "pgvector=enabled" not in log_text

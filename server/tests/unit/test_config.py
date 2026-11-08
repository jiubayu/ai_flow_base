import pytest

from src.core.config import ConfigError, load_config, parse_env_file


def full_env(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "BACKEND_HOST=127.0.0.1\n"
        "BACKEND_PORT=8000\n"
        "LOG_DIR=logs\n"
        "RUNTIME_DIR=.runtime\n"
        "CELERY_BROKER_URL=filesystem://\n"
        "CELERY_BROKER_DIR=.runtime/celery-queue\n"
        "CELERY_RESULT_DB_PATH=results.db\n"
        "DATABASE_URL=postgresql+psycopg://ai_flow:ai_flow@127.0.0.1:5432/ai_flow\n"
    )
    return env


def test_parse_env_file_skips_comments_and_blanks(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\n\nBACKEND_PORT=9000\n")
    assert parse_env_file(env) == {"BACKEND_PORT": "9000"}


def test_missing_env_file_fails(tmp_path):
    with pytest.raises(ConfigError, match="配置文件缺失"):
        load_config(tmp_path / "missing.env")


def test_missing_required_key_fails(tmp_path):
    env = full_env(tmp_path)
    env.write_text(env.read_text().replace("BACKEND_PORT=8000", ""))
    with pytest.raises(ConfigError, match="BACKEND_PORT"):
        load_config(env)


def test_non_integer_port_fails(tmp_path):
    env = full_env(tmp_path)
    env.write_text(env.read_text().replace("BACKEND_PORT=8000", "BACKEND_PORT=abc"))
    with pytest.raises(ConfigError, match="必须是整数"):
        load_config(env)


def test_optional_defaults(tmp_path):
    config = load_config(full_env(tmp_path))
    assert config.frontend_port == 5173
    assert config.debug is False


def test_load_config_uses_database_url(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "BACKEND_HOST=127.0.0.1\n"
        "BACKEND_PORT=8000\n"
        "LOG_DIR=logs\n"
        "RUNTIME_DIR=.runtime\n"
        "CELERY_BROKER_URL=filesystem://\n"
        "CELERY_BROKER_DIR=.runtime/celery-queue\n"
        "DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/ai_flow_test\n"
    )

    config = load_config(env)

    assert config.database_url == "postgresql+psycopg://user:pass@localhost:5432/ai_flow_test"

def test_load_config_requires_database_url(tmp_path):
    env = full_env(tmp_path)
    env.write_text(env.read_text().replace("DATABASE_URL=postgresql+psycopg://ai_flow:ai_flow@127.0.0.1:5432/ai_flow\n", ""))
    with pytest.raises(ConfigError, match="DATABASE_URL"):
        load_config(env)


def test_load_config_environment_overrides_file(tmp_path, monkeypatch):
    env = full_env(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://ci:ci@db:5432/ci_db")

    config = load_config(env)

    assert config.database_url == "postgresql+psycopg://ci:ci@db:5432/ci_db"


def test_config_no_longer_exposes_result_db_path(tmp_path):
    config = load_config(full_env(tmp_path))

    assert not hasattr(config, "celery_result_db_path")

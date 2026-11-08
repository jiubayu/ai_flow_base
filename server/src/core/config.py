from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = (
    "BACKEND_HOST",
    "BACKEND_PORT",
    "LOG_DIR",
    "RUNTIME_DIR",
    "CELERY_BROKER_URL",
    "CELERY_BROKER_DIR",
    "DATABASE_URL",
)


class ConfigError(RuntimeError):
    """配置缺失或无效时显式失败，不做静默兜底。"""


def _positive_int(values: dict[str, str], key: str, default: int) -> int:
    raw = values.get(key, "")
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} 必须是整数，当前值：{raw}") from exc
    if parsed <= 0:
        raise ConfigError(f"{key} 必须为正整数，当前值：{raw}")
    return parsed


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@dataclass(frozen=True)
class Config:
    server_root: Path
    backend_host: str
    backend_port: int
    frontend_port: int
    log_dir: Path
    runtime_dir: Path
    celery_broker_url: str
    celery_broker_dir: Path
    database_url: str
    debug: bool = False
    frontend_origin: str = "http://127.0.0.1:5173"
    auth_access_ttl_minutes: int = 15
    auth_refresh_ttl_days: int = 14
    auth_code_ttl_minutes: int = 10
    auth_code_min_interval_seconds: int = 60
    auth_code_window_seconds: int = 900
    auth_code_window_limit: int = 5
    auth_cookie_secure: bool = False
    # 临时本地开关：跳过邮箱验证码校验与发送，仅用于验证注册/登录主流程
    auth_skip_code_verification: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = ""


def load_config(env_path: Path | None = None) -> Config:
    env_path = env_path or SERVER_ROOT / ".env"
    if not env_path.exists():
        raise ConfigError(
            f"配置文件缺失：{env_path}。请先执行 cp server/.env.example server/.env 并填写必填项。"
        )
    values = parse_env_file(env_path)
    for key in REQUIRED_KEYS:
        env_value = os.environ.get(key)
        if env_value:
            values[key] = env_value
    missing = [key for key in REQUIRED_KEYS if not values.get(key)]
    if missing:
        raise ConfigError("缺少必填配置项：" + ", ".join(missing))
    try:
        backend_port = int(values["BACKEND_PORT"])
    except ValueError as exc:
        raise ConfigError(f"BACKEND_PORT 必须是整数，当前值：{values['BACKEND_PORT']}") from exc
    server_root = env_path.parent
    return Config(
        server_root=server_root,
        backend_host=values["BACKEND_HOST"],
        backend_port=backend_port,
        frontend_port=int(values.get("FRONTEND_PORT", "5173")),
        log_dir=server_root / values["LOG_DIR"],
        runtime_dir=server_root / values["RUNTIME_DIR"],
        celery_broker_url=values["CELERY_BROKER_URL"],
        celery_broker_dir=server_root / values["CELERY_BROKER_DIR"],
        database_url=values["DATABASE_URL"],
        debug=values.get("DEBUG", "false").lower() == "true",
        frontend_origin=values.get("FRONTEND_ORIGIN", "http://127.0.0.1:5173"),
        auth_access_ttl_minutes=_positive_int(values, "AUTH_ACCESS_TTL_MINUTES", 15),
        auth_refresh_ttl_days=_positive_int(values, "AUTH_REFRESH_TTL_DAYS", 14),
        auth_code_ttl_minutes=_positive_int(values, "AUTH_CODE_TTL_MINUTES", 10),
        auth_code_min_interval_seconds=_positive_int(values, "AUTH_CODE_MIN_INTERVAL_SECONDS", 60),
        auth_code_window_seconds=_positive_int(values, "AUTH_CODE_WINDOW_SECONDS", 900),
        auth_code_window_limit=_positive_int(values, "AUTH_CODE_WINDOW_LIMIT", 5),
        auth_cookie_secure=values.get("AUTH_COOKIE_SECURE", "false").lower() == "true",
        auth_skip_code_verification=values.get("AUTH_SKIP_CODE_VERIFICATION", "false").lower() == "true",
        smtp_host=values.get("SMTP_HOST", ""),
        smtp_port=_positive_int(values, "SMTP_PORT", 587),
        smtp_username=values.get("SMTP_USERNAME", ""),
        smtp_password=values.get("SMTP_PASSWORD", ""),
        smtp_from_address=values.get("SMTP_FROM_ADDRESS", ""),
    )

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from src.core.config import Config
from src.domain.bootstrap.entities import ServiceDefinition, ServiceRuntimeStatus
from src.domain.bootstrap.value_objects import ServiceName, ServiceState


def service_definitions(config: Config) -> tuple[ServiceDefinition, ...]:
    repo_root = config.server_root.parent
    return (
        ServiceDefinition(
            name=ServiceName.BACKEND,
            workdir=config.server_root,
            start_command=f"uv run uvicorn src.main:app --host {config.backend_host} --port {config.backend_port}",
            health_probe=f"http://{config.backend_host}:{config.backend_port}/api/health",
            log_path=config.log_dir / "backend.log",
            pid_path=config.runtime_dir / "backend.pid",
        ),
        ServiceDefinition(
            name=ServiceName.CELERY,
            workdir=config.server_root,
            start_command="uv run celery -A src.celery_app:app worker -l info",
            health_probe="",
            log_path=config.log_dir / "celery.log",
            pid_path=config.runtime_dir / "celery.pid",
            dependencies=(ServiceName.BACKEND,),
        ),
        ServiceDefinition(
            name=ServiceName.FRONTEND,
            workdir=repo_root / "ui",
            start_command="pnpm dev",
            health_probe=f"http://{config.backend_host}:{config.frontend_port}",
            log_path=config.log_dir / "frontend.log",
            pid_path=config.runtime_dir / "frontend.pid",
        ),
    )


def read_status(definition: ServiceDefinition) -> ServiceRuntimeStatus:
    now = datetime.now(timezone.utc)
    pid = None
    if definition.pid_path.exists():
        raw = definition.pid_path.read_text(encoding="utf-8").strip()
        if raw.isdigit():
            pid = int(raw)
    if pid is None:
        state, message = ServiceState.STOPPED, "未由 devctl 启动"
    elif _process_alive(pid):
        state, message = ServiceState.RUNNING, f"进程存活（PID {pid}）"
    else:
        state, message = ServiceState.FAILED, f"PID {pid} 已失效，需要清理"
    return ServiceRuntimeStatus(definition.name, state, pid, now, message)


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

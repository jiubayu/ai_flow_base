from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.domain.bootstrap.value_objects import ServiceName, ServiceState, TaskState


@dataclass
class DemoTask:
    task_id: str
    message: str
    submitted_at: datetime
    state: TaskState = TaskState.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_message: str | None = None
    error_message: str | None = None

    def mark_started(self, now: datetime) -> None:
        if self.state is not TaskState.PENDING:
            raise ValueError(f"任务 {self.task_id} 无法从 {self.state.value} 进入 STARTED")
        self.state = TaskState.STARTED
        self.started_at = now

    def mark_success(self, result_message: str, now: datetime) -> None:
        if self.state is not TaskState.STARTED:
            raise ValueError(f"任务 {self.task_id} 无法从 {self.state.value} 进入 SUCCESS")
        self.state = TaskState.SUCCESS
        self.result_message = result_message
        self.finished_at = now

    def mark_failure(self, error_message: str, now: datetime) -> None:
        if self.state is not TaskState.STARTED:
            raise ValueError(f"任务 {self.task_id} 无法从 {self.state.value} 进入 FAILURE")
        if not error_message:
            raise ValueError("FAILURE 状态必须记录 error_message")
        self.state = TaskState.FAILURE
        self.error_message = error_message
        self.finished_at = now


@dataclass(frozen=True)
class ServiceDefinition:
    name: ServiceName
    workdir: Path
    start_command: str
    health_probe: str
    log_path: Path
    pid_path: Path
    dependencies: tuple[ServiceName, ...] = ()


@dataclass
class ServiceRuntimeStatus:
    service_name: ServiceName
    state: ServiceState
    pid: int | None
    last_check_at: datetime
    status_message: str

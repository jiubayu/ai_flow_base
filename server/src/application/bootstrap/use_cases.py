from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from src.application.bootstrap.errors import TaskNotFoundError
from src.core.config import Config
from src.domain.bootstrap.entities import DemoTask
from src.domain.bootstrap.value_objects import TaskState
from src.infrastructure.persistence.result_store import PostgresDemoTaskResultStore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_startup(config: Config) -> Config:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    config.runtime_dir.mkdir(parents=True, exist_ok=True)
    return config


class DemoTaskUseCase:
    def __init__(self, store: PostgresDemoTaskResultStore, dispatch: Callable[[str, str], None] | None = None) -> None:
        self.store = store
        self.dispatch = dispatch

    def submit(self, message: str) -> DemoTask:
        task = DemoTask(
            task_id=str(uuid4()),
            message=message,
            submitted_at=utcnow(),
            state=TaskState.PENDING,
        )
        self.store.save(task)
        if self.dispatch is not None:
            self.dispatch(task.task_id, message)
        return task

    def get(self, task_id: str) -> DemoTask:
        task = self.store.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def process(self, task_id: str, message: str) -> str:
        task = self.get(task_id)
        task.mark_started(utcnow())
        self.store.save(task)
        try:
            result_message = f"processed: {message}"
            task.mark_success(result_message, utcnow())
            self.store.save(task)
            return result_message
        except Exception as exc:
            task.mark_failure(str(exc), utcnow())
            self.store.save(task)
            raise

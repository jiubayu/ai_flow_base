from __future__ import annotations

from sqlalchemy import select

from src.domain.bootstrap.entities import DemoTask
from src.domain.bootstrap.value_objects import TaskState
from src.infrastructure.persistence.database import SessionFactory
from src.infrastructure.persistence.models import DemoTaskModel


class PostgresDemoTaskResultStore:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def save(self, task: DemoTask) -> None:
        with self._session_factory.begin() as session:
            row = session.get(DemoTaskModel, task.task_id)
            if row is None:
                session.add(
                    DemoTaskModel(
                        task_id=task.task_id,
                        message=task.message,
                        submitted_at=task.submitted_at,
                        started_at=task.started_at,
                        finished_at=task.finished_at,
                        state=task.state.value,
                        result_message=task.result_message,
                        error_message=task.error_message,
                    )
                )
            else:
                row.message = task.message
                row.submitted_at = task.submitted_at
                row.started_at = task.started_at
                row.finished_at = task.finished_at
                row.state = task.state.value
                row.result_message = task.result_message
                row.error_message = task.error_message

    def get(self, task_id: str) -> DemoTask | None:
        with self._session_factory() as session:
            row = session.scalar(select(DemoTaskModel).where(DemoTaskModel.task_id == task_id))
        if row is None:
            return None
        return DemoTask(
            task_id=row.task_id,
            message=row.message,
            submitted_at=row.submitted_at,
            state=TaskState(row.state),
            started_at=row.started_at,
            finished_at=row.finished_at,
            result_message=row.result_message,
            error_message=row.error_message,
        )

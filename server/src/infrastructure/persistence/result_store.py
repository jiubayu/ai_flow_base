from __future__ import annotations

from pathlib import Path

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from src.domain.bootstrap.entities import DemoTask
from src.domain.bootstrap.value_objects import TaskState


class Base(DeclarativeBase):
    pass


class DemoTaskRecord(Base):
    __tablename__ = "demo_tasks"

    task_id = Column(String, primary_key=True)
    message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    state = Column(String, nullable=False)
    result_message = Column(Text)
    error_message = Column(Text)


class ResultStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", future=True)
        Base.metadata.create_all(self.engine)

    def save(self, task: DemoTask) -> None:
        with Session(self.engine) as session:
            record = session.get(DemoTaskRecord, task.task_id)
            if record is None:
                record = DemoTaskRecord(task_id=task.task_id)
            record.message = task.message
            record.submitted_at = task.submitted_at
            record.started_at = task.started_at
            record.finished_at = task.finished_at
            record.state = task.state.value
            record.result_message = task.result_message
            record.error_message = task.error_message
            session.add(record)
            session.commit()

    def get(self, task_id: str) -> DemoTask | None:
        with Session(self.engine) as session:
            record = session.get(DemoTaskRecord, task_id)
            if record is None:
                return None
            return DemoTask(
                task_id=record.task_id,
                message=record.message,
                submitted_at=record.submitted_at,
                state=TaskState(record.state),
                started_at=record.started_at,
                finished_at=record.finished_at,
                result_message=record.result_message,
                error_message=record.error_message,
            )

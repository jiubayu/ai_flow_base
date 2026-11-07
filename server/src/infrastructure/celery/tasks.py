from __future__ import annotations

from src.application.bootstrap.use_cases import DemoTaskUseCase
from src.celery_app import app
from src.core.config import load_config
from src.infrastructure.persistence.database import create_database_engine, create_session_factory
from src.infrastructure.persistence.result_store import PostgresDemoTaskResultStore


@app.task(name="bootstrap.demo_task")
def demo_task(task_id: str, message: str) -> str:
    config = load_config()
    session_factory = create_session_factory(create_database_engine(config))
    use_case = DemoTaskUseCase(PostgresDemoTaskResultStore(session_factory))
    return use_case.process(task_id, message)

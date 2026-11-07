from __future__ import annotations

from src.application.bootstrap.use_cases import DemoTaskUseCase
from src.celery_app import app
from src.core.config import load_config
from src.infrastructure.persistence.result_store import ResultStore


@app.task(name="bootstrap.demo_task")
def demo_task(task_id: str, message: str) -> str:
    config = load_config()
    use_case = DemoTaskUseCase(ResultStore(config.celery_result_db_path))
    return use_case.process(task_id, message)

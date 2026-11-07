from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from src.application.bootstrap.use_cases import DemoTaskUseCase

router = APIRouter(prefix="/api/dev/tasks")


class DemoTaskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=120)


@router.post("/demo", status_code=202)
def submit_demo_task(body: DemoTaskRequest, request: Request) -> dict:
    use_case = DemoTaskUseCase(request.app.state.result_store, request.app.state.dispatch)
    task = use_case.submit(body.message)
    return {"task_id": task.task_id, "state": task.state.value, "message": task.message}


@router.get("/{task_id}")
def get_demo_task_status(task_id: str, request: Request) -> dict:
    use_case = DemoTaskUseCase(request.app.state.result_store)
    task = use_case.get(task_id)
    return {
        "task_id": task.task_id,
        "state": task.state.value,
        "result_message": task.result_message,
        "error_message": task.error_message,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }

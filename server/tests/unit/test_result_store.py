from datetime import datetime, timezone

from src.domain.bootstrap.entities import DemoTask
from src.domain.bootstrap.value_objects import TaskState
from src.infrastructure.persistence.result_store import PostgresDemoTaskResultStore


def test_result_store_persists_success(postgres_session_factory) -> None:
    store = PostgresDemoTaskResultStore(postgres_session_factory)
    now = datetime.now(timezone.utc)

    task = DemoTask(task_id="task-1", message="hello", submitted_at=now, state=TaskState.PENDING)
    store.save(task)
    task.mark_started(now)
    store.save(task)
    task.mark_success("done", now)
    store.save(task)

    saved = store.get(task.task_id)
    assert saved.state == "SUCCESS"
    assert saved.result_message == "done"
    assert saved.error_message is None


def test_get_missing_returns_none(postgres_session_factory) -> None:
    store = PostgresDemoTaskResultStore(postgres_session_factory)
    assert store.get("nope") is None


def test_update_persists_state_change(postgres_session_factory) -> None:
    store = PostgresDemoTaskResultStore(postgres_session_factory)
    now = datetime.now(timezone.utc)

    task = DemoTask(task_id="t2", message="boom", submitted_at=now, state=TaskState.PENDING)
    store.save(task)
    task.mark_started(now)
    task.mark_failure("worker error", now)
    store.save(task)

    fetched = store.get("t2")
    assert fetched.state == TaskState.FAILURE
    assert fetched.error_message == "worker error"
    assert fetched.finished_at is not None

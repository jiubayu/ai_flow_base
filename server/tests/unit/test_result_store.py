from datetime import datetime, timezone

from src.domain.bootstrap.entities import DemoTask
from src.domain.bootstrap.value_objects import TaskState
from src.infrastructure.persistence.result_store import ResultStore


def test_save_get_roundtrip(tmp_path):
    store = ResultStore(tmp_path / "results.db")
    now = datetime.now(timezone.utc)
    task = DemoTask(task_id="t1", message="hello", submitted_at=now, state=TaskState.PENDING)
    store.save(task)

    fetched = store.get("t1")
    assert fetched is not None
    assert fetched.state == TaskState.PENDING
    assert fetched.message == "hello"


def test_get_missing_returns_none(tmp_path):
    store = ResultStore(tmp_path / "results.db")
    assert store.get("nope") is None


def test_update_persists_state_change(tmp_path):
    store = ResultStore(tmp_path / "results.db")
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
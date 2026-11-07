from src.application.bootstrap.use_cases import DemoTaskUseCase
from src.domain.bootstrap.value_objects import TaskState
from src.infrastructure.persistence.result_store import PostgresDemoTaskResultStore


def test_backend_to_celery_demo_task_flow(postgres_session_factory):
    store = PostgresDemoTaskResultStore(postgres_session_factory)
    use_case = DemoTaskUseCase(store)

    def fake_worker(task_id: str, message: str) -> None:
        use_case.process(task_id, message)

    use_case.dispatch = fake_worker
    accepted = use_case.submit("bootstrap smoke")
    assert accepted.state == TaskState.PENDING

    processed = use_case.get(accepted.task_id)
    assert processed.state == TaskState.SUCCESS
    assert processed.result_message == "processed: bootstrap smoke"
    assert processed.started_at is not None
    assert processed.finished_at is not None


def test_demo_task_flow_failure_records_error(postgres_session_factory):
    store = PostgresDemoTaskResultStore(postgres_session_factory)
    use_case = DemoTaskUseCase(store)
    accepted = use_case.submit("boom")
    task = use_case.get(accepted.task_id)
    task.mark_started(task.submitted_at)
    task.mark_failure("worker error", task.submitted_at)
    store.save(task)

    fetched = use_case.get(accepted.task_id)
    assert fetched.state == TaskState.FAILURE
    assert fetched.error_message == "worker error"

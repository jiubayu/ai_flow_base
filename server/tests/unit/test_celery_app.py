from src.celery_app import create_celery_app


def test_celery_result_backend_uses_postgres(config) -> None:
    celery = create_celery_app(config)

    assert celery.conf.result_backend == f"db+{config.database_url}"

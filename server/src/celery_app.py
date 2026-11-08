from __future__ import annotations

from celery import Celery

from src.core.config import Config, load_config
from src.infrastructure.celery.broker import ensure_broker_dir, transport_options


def create_celery_app(config: Config) -> Celery:
    ensure_broker_dir(config.celery_broker_dir)
    celery = Celery("bootstrap")
    celery.conf.broker_url = config.celery_broker_url
    celery.conf.result_backend = f"db+{config.database_url}"
    celery.conf.broker_transport_options = transport_options(config.celery_broker_dir)
    return celery


app = create_celery_app(load_config())

from src.infrastructure.celery import tasks  # noqa: E402,F401 注册任务

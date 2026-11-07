from enum import Enum


class TaskState(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ServiceState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ServiceName(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    CELERY = "celery"

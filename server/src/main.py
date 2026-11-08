from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.application.auth.errors import AuthError, RateLimitedError
from src.application.auth.services import EmailSender
from src.application.auth.use_cases import AuthUseCase
from src.application.bootstrap.errors import TaskNotFoundError
from src.application.bootstrap.use_cases import validate_startup
from src.application.workspace.errors import WorkspaceError
from src.application.workspace.use_cases import WorkspaceUseCase
from src.core.config import Config, load_config
from src.core.logging import configure_logging
from src.domain.auth.services import RateLimitPolicy
from src.infrastructure.clock import SystemClock
from src.infrastructure.logging.file_logger import FileLogger
from src.infrastructure.persistence.auth_repository import PostgresAuthRepository
from src.infrastructure.persistence.database import create_database_engine, create_session_factory
from src.infrastructure.persistence.result_store import PostgresDemoTaskResultStore
from src.infrastructure.persistence.workspace_repository import PostgresWorkspaceRepository
from src.presentation.api import auth, dev_tasks, health, workspace


def default_dispatch(task_id: str, message: str) -> None:
    from src.infrastructure.celery.tasks import demo_task

    demo_task.delay(task_id, message)


def _default_email_sender(config: Config, logger) -> EmailSender:
    from src.infrastructure.security.password_hasher import ScryptPasswordHasher
    from src.infrastructure.security.cookie_session_manager import CookieSessionManager
    from src.infrastructure.messaging.smtp_email_sender import SmtpEmailSender

    return SmtpEmailSender(config, logger)


def build_services(
    config: Config,
    logger,
    *,
    clock=None,
    auth_sender: EmailSender | None = None,
    session_factory,
) -> tuple[AuthUseCase, WorkspaceUseCase]:
    from src.infrastructure.security.cookie_session_manager import CookieSessionManager
    from src.infrastructure.security.password_hasher import ScryptPasswordHasher

    auth_repo = PostgresAuthRepository(session_factory, logger)
    workspace_repo = PostgresWorkspaceRepository(session_factory, logger)

    clock = clock or SystemClock()
    workspace_use_case = WorkspaceUseCase(workspace_repo, clock, logger)
    auth_use_case = AuthUseCase(
        auth_repo,
        auth_sender or _default_email_sender(config, logger),
        clock,
        ScryptPasswordHasher(),
        CookieSessionManager(secure=config.auth_cookie_secure),
        access_ttl_seconds=config.auth_access_ttl_minutes * 60,
        refresh_ttl_seconds=config.auth_refresh_ttl_days * 86400,
        code_ttl_seconds=config.auth_code_ttl_minutes * 60,
        rate_limit=RateLimitPolicy(
            min_interval_seconds=config.auth_code_min_interval_seconds,
            window_seconds=config.auth_code_window_seconds,
            window_limit=config.auth_code_window_limit,
        ),
        logger=logger,
        workspace=workspace_use_case,
        skip_code_verification=config.auth_skip_code_verification,
    )
    return auth_use_case, workspace_use_case


def create_app(
    config: Config | None = None,
    dispatch: Callable[[str, str], None] | None = None,
    *,
    auth_sender: EmailSender | None = None,
    clock=None,
) -> FastAPI:
    config = config or load_config()
    validate_startup(config)

    app = FastAPI(title="Bootstrap Development API")
    app.state.config = config

    engine = create_database_engine(config)
    session_factory = create_session_factory(engine)
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.result_store = PostgresDemoTaskResultStore(session_factory)
    app.state.dispatch = dispatch or default_dispatch

    logger = configure_logging(FileLogger(config.log_dir / "backend.log"), "backend", config.debug)
    app.state.logger = logger
    logger.info(f"后端服务启动：http://{config.backend_host}:{config.backend_port}")

    auth_use_case, workspace_use_case = build_services(
        config, logger, clock=clock, auth_sender=auth_sender, session_factory=session_factory
    )
    app.state.auth_use_case = auth_use_case
    app.state.workspace_use_case = workspace_use_case
    logger.info(
        "认证初始化完成："
        f"access TTL {config.auth_access_ttl_minutes} 分钟，"
        f"refresh TTL {config.auth_refresh_ttl_days} 天，"
        f"code TTL {config.auth_code_ttl_minutes} 分钟，"
        f"限流 {config.auth_code_min_interval_seconds}s/{config.auth_code_window_seconds}s≤{config.auth_code_window_limit}，"
        f"cookie secure={config.auth_cookie_secure}"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(dev_tasks.router)
    app.include_router(auth.router)
    app.include_router(workspace.router)
    app.include_router(workspace.apps_router)

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": {"code": "task_not_found", "message": str(exc)}},
        )

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
        detail = {"code": exc.code, "message": exc.message}
        if isinstance(exc, RateLimitedError):
            detail["retry_after_seconds"] = exc.retry_after_seconds
        logger.debug(f"认证失败：{exc.code} - {exc.message}")
        return JSONResponse(status_code=exc.status, content={"detail": detail})

    @app.exception_handler(WorkspaceError)
    async def workspace_error_handler(request: Request, exc: WorkspaceError) -> JSONResponse:
        logger.debug(f"工作空间操作失败：{exc.code} - {exc.message}")
        return JSONResponse(status_code=exc.status, content={"detail": {"code": exc.code, "message": exc.message}})

    return app


app = create_app()

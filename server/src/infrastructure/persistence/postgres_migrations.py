from __future__ import annotations

from sqlalchemy import Engine, inspect, text

from src.infrastructure.persistence.models import Base

REQUIRED_TABLES = {
    "user_accounts",
    "email_verification_challenges",
    "refresh_grants",
    "auth_sessions",
    "auth_audit_events",
    "workspaces",
    "workspace_memberships",
    "user_workspace_preferences",
    "workspace_audit_events",
    "workspace_applications",
    "workflow_test_runs",
    "workflow_test_run_nodes",
    "workspace_knowledge_bases",
    "workspace_knowledge_documents",
    "workspace_model_provider_configs",
    "demo_tasks",
}


def initialize_postgres_schema(engine: Engine) -> list[str]:
    """幂等初始化 PostgreSQL schema：vector 扩展与全部 ORM 表。"""
    executed: list[str] = []
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        executed.append("CREATE EXTENSION vector")
        Base.metadata.create_all(connection)
        executed.append("Base.metadata.create_all")
    return executed


def verify_postgres_schema(engine: Engine) -> dict[str, bool]:
    """检查 vector 扩展与必需表是否存在；这是本任务持久层唯一允许的裸 SQL。"""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.connect() as connection:
        vector_enabled = connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        ).scalar_one()
    return {
        "vector_extension": bool(vector_enabled),
        **{f"{table_name}_table": table_name in table_names for table_name in sorted(REQUIRED_TABLES)},
    }

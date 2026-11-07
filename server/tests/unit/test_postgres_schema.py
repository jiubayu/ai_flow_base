from __future__ import annotations

from sqlalchemy import create_engine, inspect

from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.postgres_migrations import (
    initialize_postgres_schema,
    verify_postgres_schema,
)


def test_metadata_defines_required_tables() -> None:
    table_names = set(Base.metadata.tables)

    assert {
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
    }.issubset(table_names)


def test_initialize_postgres_schema_creates_tables_and_vector(postgres_engine) -> None:
    engine = postgres_engine
    executed = initialize_postgres_schema(engine)
    verification = verify_postgres_schema(engine)

    inspector = inspect(engine)
    assert "CREATE EXTENSION vector" in executed
    assert "user_accounts" in inspector.get_table_names()
    assert verification["vector_extension"] is True
    assert all(verification.values())

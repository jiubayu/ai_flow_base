from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

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


def test_app_uses_postgres_session_factory(app) -> None:
    assert hasattr(app.state, "db_engine")
    assert hasattr(app.state, "db_session_factory")


def test_postgres_test_fixture_uses_isolated_schema(postgres_engine) -> None:
    with postgres_engine.connect() as connection:
        schema = connection.exec_driver_sql("SELECT current_schema()").scalar_one()

    assert schema.startswith("test_")


def test_app_fixture_uses_isolated_schema(app) -> None:
    with app.state.db_engine.connect() as connection:
        schema = connection.exec_driver_sql("SELECT current_schema()").scalar_one()

    assert schema.startswith("test_")


def test_tables_are_created_in_the_test_schema(postgres_engine) -> None:
    # Issue 4: metadata.schema is captured at model-definition time, so setting it after
    # import does not move already-defined tables. Isolation must come from creating the
    # tables through search_path into the per-test schema — assert that outcome directly.
    schema = make_url(postgres_engine.url).query["options"].removeprefix("-csearch_path=").split(",", 1)[0]

    assert len(inspect(postgres_engine).get_table_names(schema=schema)) == 16

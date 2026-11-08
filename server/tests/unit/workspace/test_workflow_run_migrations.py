from src.infrastructure.persistence.postgres_migrations import verify_postgres_schema


def test_postgres_schema_contains_workspace_workflow_tables(postgres_engine) -> None:
    verification = verify_postgres_schema(postgres_engine)

    assert verification["workspace_applications_table"] is True
    assert verification["workflow_test_runs_table"] is True
    assert verification["workflow_test_run_nodes_table"] is True
    assert verification["workspace_knowledge_bases_table"] is True
    assert verification["workspace_knowledge_documents_table"] is True

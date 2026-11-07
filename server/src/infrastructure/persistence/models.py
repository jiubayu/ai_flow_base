from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserAccountModel(Base):
    __tablename__ = "user_accounts"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash_version: Mapped[str] = mapped_column(String(64), nullable=False)
    password_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmailVerificationChallengeModel(Base):
    __tablename__ = "email_verification_challenges"
    __table_args__ = (Index("ix_challenges_email_purpose_state", "email", "purpose", "state"),)

    challenge_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    code_digest: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_send_count: Mapped[int] = mapped_column(Integer, nullable=False)
    verify_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[str] = mapped_column(String(255), nullable=False)


class RefreshGrantModel(Base):
    __tablename__ = "refresh_grants"
    __table_args__ = (Index("ix_refresh_grants_user_scope_state", "user_id", "client_scope", "state"),)

    refresh_grant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), nullable=False)
    client_scope: Mapped[str] = mapped_column(String(255), nullable=False)
    rotated_from_id: Mapped[str | None] = mapped_column(String(36))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[str | None] = mapped_column(String(36))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(255), nullable=False)


class AuthSessionModel(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_grant", "refresh_grant_id"),)

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), nullable=False)
    refresh_grant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("refresh_grants.refresh_grant_id"), nullable=False
    )
    client_scope: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(255), nullable=False)


class AuthAuditEventModel(Base):
    __tablename__ = "auth_audit_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user_accounts.user_id"))
    email: Mapped[str | None] = mapped_column(String(255))
    client_scope: Mapped[str | None] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome_code: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    workspace_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)


class WorkspaceMembershipModel(Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = (
        Index("idx_workspace_memberships_user_status", "user_id", "status"),
        Index(
            "idx_workspace_memberships_active_user",
            "workspace_id",
            "user_id",
            unique=True,
            postgresql_where=text("status") == "active",
        ),
        Index("ix_memberships_workspace_status_role", "workspace_id", "status", "role"),
    )

    membership_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user_accounts.user_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserWorkspacePreferenceModel(Base):
    __tablename__ = "user_workspace_preferences"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), primary_key=True)
    last_workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkspaceAuditEventModel(Base):
    __tablename__ = "workspace_audit_events"
    __table_args__ = (Index("ix_workspace_audit_workspace_occurred", "workspace_id", "occurred_at"),)

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"))
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user_accounts.user_id"))
    target_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user_accounts.user_id"))
    outcome_code: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkspaceApplicationModel(Base):
    __tablename__ = "workspace_applications"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="ux_workspace_applications_name"),
        Index("ix_workspace_applications_workspace", "workspace_id", "updated_at"),
    )

    application_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkflowTestRunModel(Base):
    __tablename__ = "workflow_test_runs"
    __table_args__ = (Index("idx_workflow_test_runs_application_started", "application_id", "started_at"),)

    workflow_run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace_applications.application_id"), nullable=False
    )
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    final_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    variables_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    workflow_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)


class WorkflowTestRunNodeModel(Base):
    __tablename__ = "workflow_test_run_nodes"
    __table_args__ = (Index("idx_workflow_test_run_nodes_run_node", "workflow_run_id", "node_id"),)

    node_run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflow_test_runs.workflow_run_id"), nullable=False
    )
    node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)


class WorkspaceKnowledgeBaseModel(Base):
    __tablename__ = "workspace_knowledge_bases"
    __table_args__ = (Index("idx_knowledge_bases_workspace", "workspace_id"),)

    knowledge_base_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkspaceKnowledgeDocumentModel(Base):
    __tablename__ = "workspace_knowledge_documents"
    __table_args__ = (Index("idx_knowledge_documents_kb", "knowledge_base_id", "created_at"),)

    document_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace_knowledge_bases.knowledge_base_id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkspaceModelProviderConfigModel(Base):
    __tablename__ = "workspace_model_provider_configs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "provider", name="ux_model_provider_configs_workspace_provider"),
    )

    config_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.workspace_id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    default_model: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    rerank_model: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    rerank_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_test_status: Mapped[str | None] = mapped_column(String(255))
    last_test_message: Mapped[str | None] = mapped_column(Text)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DemoTaskModel(Base):
    __tablename__ = "demo_tasks"

    task_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    result_message: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

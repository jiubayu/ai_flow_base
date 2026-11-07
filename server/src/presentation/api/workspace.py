from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from src.application.auth.errors import UnauthorizedError
from src.application.workspace.errors import WorkspaceSessionExpiredError, WorkspaceSessionMissingError
from src.application.workspace.ports import WorkspaceMemberView, WorkspaceSummary
from src.application.workspace.use_cases import WorkspaceContextResult
from src.domain.workspace.entities import Workspace, WorkspaceApplication

router = APIRouter(prefix="/api/workspaces", tags=["workspace"])

# 005：应用工作空间路由（单数 /api/workspace），与 004 的 /api/workspaces 共存。
apps_router = APIRouter(prefix="/api/workspace", tags=["workspace-applications"])


class SwitchWorkspaceRequest(BaseModel):
    workspace_id: str = Field(min_length=1)


class AddMemberRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    role: str = Field(pattern=r"^(manager|member)$")


class ChangeRoleRequest(BaseModel):
    role: str = Field(pattern=r"^(manager|member)$")


def _workspace_payload(summary: WorkspaceSummary) -> dict:
    return {
        "workspace_id": summary.workspace_id,
        "name": summary.name,
        "role": summary.role,
        "is_current": summary.is_current,
    }


def _context_payload(context: WorkspaceContextResult) -> dict:
    return {
        "current": _workspace_payload(context.current) if context.current else None,
        "available": [_workspace_payload(item) for item in context.available],
    }


def _member_payload(member: WorkspaceMemberView) -> dict:
    return {
        "user_id": member.user_id,
        "username": member.username,
        "role": member.role,
        "joined_at": member.joined_at.isoformat(),
    }


def _current_user_id(request: Request) -> str:
    auth = request.app.state.auth_use_case
    session_id, _ = auth.cookies.read(request.cookies)
    if not session_id:
        raise WorkspaceSessionMissingError("当前浏览器没有登录状态，请重新登录")
    try:
        result = auth.current_session(session_id)
    except UnauthorizedError:
        raise WorkspaceSessionExpiredError("当前浏览器会话已过期，请重新登录")
    return result.user.user_id


@router.get("")
async def list_workspaces(request: Request):
    user_id = _current_user_id(request)
    return {"workspaces": [_workspace_payload(item) for item in request.app.state.workspace_use_case.list_workspaces(user_id).available]}


@router.post("/current")
async def switch_current_workspace(request: Request, body: SwitchWorkspaceRequest):
    user_id = _current_user_id(request)
    return _context_payload(request.app.state.workspace_use_case.switch_workspace(user_id, body.workspace_id))


@router.get("/current/members")
async def list_members(request: Request):
    user_id = _current_user_id(request)
    members = request.app.state.workspace_use_case.list_members(user_id)
    return {"members": [_member_payload(member) for member in members]}


@router.post("/current/members", status_code=201)
async def add_member(request: Request, body: AddMemberRequest):
    user_id = _current_user_id(request)
    member = request.app.state.workspace_use_case.add_member(user_id, body.username, body.role)
    return {"member": _member_payload(member)}


@router.patch("/current/members/{user_id}")
async def change_member_role(request: Request, user_id: str, body: ChangeRoleRequest):
    actor_id = _current_user_id(request)
    member = request.app.state.workspace_use_case.change_role(actor_id, user_id, body.role)
    return {"member": _member_payload(member)}


@router.delete("/current/members/{user_id}", status_code=204)
async def remove_member(request: Request, user_id: str):
    actor_id = _current_user_id(request)
    request.app.state.workspace_use_case.remove_member(actor_id, user_id)
    return None


# ----------------------------------------------------------------------
# 005：默认工作空间概览与应用（contracts/workspace-api.openapi.yaml）
# ----------------------------------------------------------------------


class CreateApplicationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class UpdateApplicationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=500)


def _workspace_overview_payload(workspace: Workspace) -> dict:
    return {
        "workspace_id": workspace.workspace_id,
        "name": workspace.name,
        "is_default": True,
        "created_at": workspace.created_at.isoformat(),
        "updated_at": workspace.updated_at.isoformat(),
    }


def _application_card_payload(application: WorkspaceApplication) -> dict:
    return {
        "application_id": application.application_id,
        "name": application.name,
        "description": application.description,
        "status": application.status.value,
        "updated_at": application.updated_at.isoformat(),
    }


def _application_detail_payload(application: WorkspaceApplication) -> dict:
    payload = _application_card_payload(application)
    payload["created_at"] = application.created_at.isoformat()
    return payload


def _application_detail_response(application: WorkspaceApplication) -> dict:
    canvas = application.to_canvas_view()
    return {
        "application": _application_detail_payload(application),
        "canvas": {
            "mode": canvas.mode,
            "editable": canvas.editable,
            "entry_label": canvas.entry_label,
        },
    }


@apps_router.get("/current")
async def get_current_workspace(request: Request):
    user_id = _current_user_id(request)
    overview = request.app.state.workspace_use_case.get_workspace_overview(user_id)
    return {
        "workspace": _workspace_overview_payload(overview.workspace),
        "applications": [_application_card_payload(app) for app in overview.applications],
    }


@apps_router.post("/applications", status_code=201)
async def create_application(request: Request, body: CreateApplicationRequest):
    user_id = _current_user_id(request)
    application = request.app.state.workspace_use_case.create_application(
        user_id, body.name, body.description
    )
    return _application_detail_response(application)


@apps_router.get("/applications/{application_id}")
async def get_application(request: Request, application_id: str):
    user_id = _current_user_id(request)
    application = request.app.state.workspace_use_case.get_application_detail(user_id, application_id)
    return _application_detail_response(application)


@apps_router.patch("/applications/{application_id}")
async def update_application(request: Request, application_id: str, body: UpdateApplicationRequest):
    user_id = _current_user_id(request)
    application = request.app.state.workspace_use_case.update_application_summary(
        user_id, application_id, body.name, body.description
    )
    return _application_detail_response(application)

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator

from src.application.auth.use_cases import AuthSessionResult
from src.domain.auth.value_objects import is_valid_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SendEmailCodeRequest(BaseModel):
    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not is_valid_email(value):
            raise ValueError("邮箱格式无效")
        return value


class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    code: str = Field(pattern=r"^[0-9]{6}$")
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not is_valid_email(value):
            raise ValueError("邮箱格式无效")
        return value


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not is_valid_email(value):
            raise ValueError("邮箱格式无效")
        return value


def _workspace_payload(context) -> dict:
    if context is None:
        return {"current": None, "available": []}
    return {
        "current": _workspace_summary(context.current) if context.current else None,
        "available": [_workspace_summary(item) for item in context.available],
    }


def _workspace_summary(summary) -> dict:
    return {
        "workspace_id": summary.workspace_id,
        "name": summary.name,
        "role": summary.role,
        "is_current": summary.is_current,
    }


def _session_payload(result: AuthSessionResult) -> dict:
    return {
        "user": {
            "user_id": result.user.user_id,
            "email": result.user.email,
            "email_verified": result.user.email_verified,
            "username": result.user.username,
        },
        "session": {
            "authenticated": True,
            "access_expires_at": result.session.access_expires_at.isoformat(),
            "refresh_expires_at": result.session.refresh_expires_at.isoformat(),
        },
        "workspace": _workspace_payload(result.workspace),
    }


def _json_with_cookies(status_code: int, content: dict, cookies: tuple[str, ...]) -> Response:
    response = JSONResponse(status_code=status_code, content=content)
    for cookie in cookies:
        response.headers.append("Set-Cookie", cookie)
    return response


def _use_case(request: Request):
    return request.app.state.auth_use_case


@router.post("/email-code", status_code=202)
async def send_email_code(request: Request, body: SendEmailCodeRequest):
    accepted = _use_case(request).send_code(body.email)
    return {
        "status": "accepted",
        "retry_after_seconds": accepted.retry_after_seconds,
        "expires_in_seconds": accepted.expires_in_seconds,
    }


@router.post("/register", status_code=201)
async def register(request: Request, body: RegisterRequest):
    result = _use_case(request).register(body.email, body.code, body.password)
    return _json_with_cookies(201, _session_payload(result), result.set_cookies)


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    result = _use_case(request).login(body.email, body.password)
    return _json_with_cookies(200, _session_payload(result), result.set_cookies)


@router.get("/session")
async def get_session(request: Request):
    session_id, _ = _use_case(request).cookies.read(request.cookies)
    result = _use_case(request).current_session(session_id)
    return _session_payload(result)


@router.post("/refresh")
async def refresh(request: Request):
    _, grant_id = _use_case(request).cookies.read(request.cookies)
    result = _use_case(request).refresh(grant_id)
    return _json_with_cookies(200, _session_payload(result), result.set_cookies)


@router.post("/logout", status_code=204)
async def logout(request: Request):
    use_case = _use_case(request)
    session_id, grant_id = use_case.cookies.read(request.cookies)
    use_case.logout(session_id, grant_id)
    response = Response(status_code=204)
    for cookie in use_case.cookies.clear():
        response.headers.append("Set-Cookie", cookie)
    return response

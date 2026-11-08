from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from src.application.auth.errors import (
    EmailAlreadyRegisteredError,
    InvalidCodeError,
    PasswordPolicyError,
    RateLimitedError,
    UnauthorizedError,
)
from src.application.auth.ports import AuthRepository, Clock
from src.application.auth.services import EmailSender, PasswordHasher, SessionCookieManager
from src.application.workspace.errors import WorkspaceCreationError
from src.application.workspace.ports import WorkspaceRepositoryPort
from src.application.workspace.use_cases import WorkspaceContextResult, WorkspaceUseCase
from src.domain.auth.entities import AuthAuditEvent, AuthSession, EmailVerificationChallenge, RefreshGrant, UserAccount
from src.domain.auth.services import RateLimitPolicy, code_digest, generate_verification_code
from src.domain.auth.value_objects import AuditEventType, check_password_policy, normalize_email
from src.domain.workspace.value_objects import username_from_email

REGISTER_PURPOSE = "register"


@dataclass(frozen=True)
class UserSummary:
    user_id: str
    email: str
    email_verified: bool
    username: str = ""


@dataclass(frozen=True)
class SessionSummary:
    authenticated: bool
    access_expires_at: datetime
    refresh_expires_at: datetime


@dataclass(frozen=True)
class AuthSessionResult:
    user: UserSummary
    session: SessionSummary
    set_cookies: tuple[str, ...] = ()
    workspace: WorkspaceContextResult | None = None


@dataclass(frozen=True)
class CodeAccepted:
    retry_after_seconds: int
    expires_in_seconds: int


class AuthUseCase:
    def __init__(
        self,
        repo: AuthRepository,
        sender: EmailSender,
        clock: Clock,
        hasher: PasswordHasher,
        cookies: SessionCookieManager,
        *,
        access_ttl_seconds: int,
        refresh_ttl_seconds: int,
        code_ttl_seconds: int,
        rate_limit: RateLimitPolicy,
        logger: logging.Logger | None = None,
        workspace: WorkspaceUseCase | None = None,
        skip_code_verification: bool = False,
    ) -> None:
        self.repo = repo
        self.sender = sender
        self.clock = clock
        self.hasher = hasher
        self.cookies = cookies
        self.access_ttl_seconds = access_ttl_seconds
        self.refresh_ttl_seconds = refresh_ttl_seconds
        self.code_ttl_seconds = code_ttl_seconds
        self.rate_limit = rate_limit
        self.logger = logger
        self.workspace = workspace
        self.skip_code_verification = skip_code_verification

    def _audit(
        self,
        event_type: AuditEventType,
        *,
        outcome_code: str,
        message: str,
        user_id: str | None = None,
        email: str | None = None,
        client_scope: str | None = None,
    ) -> None:
        event = AuthAuditEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=self.clock.now(),
            outcome_code=outcome_code,
            message=message,
            user_id=user_id,
            email=email,
            client_scope=client_scope,
        )
        self.repo.record_audit(event)
        if self.logger is not None:
            self.logger.debug(f"认证审计：{event_type.value} [{outcome_code}] {message}")

    def _build_session(
        self, user: UserAccount, client_scope: str, now: datetime, rotated_from_id: str | None = None
    ) -> tuple[AuthSession, RefreshGrant]:
        grant_id = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(32)
        grant = RefreshGrant(
            refresh_grant_id=grant_id,
            user_id=user.user_id,
            client_scope=client_scope,
            rotated_from_id=rotated_from_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=self.refresh_ttl_seconds),
        )
        session = AuthSession(
            session_id=session_id,
            user_id=user.user_id,
            refresh_grant_id=grant_id,
            client_scope=client_scope,
            issued_at=now,
            expires_at=now + timedelta(seconds=self.access_ttl_seconds),
        )
        return session, grant

    def _issue_session(
        self, user: UserAccount, client_scope: str, now: datetime, rotated_from_id: str | None = None
    ) -> tuple[AuthSession, RefreshGrant]:
        session, grant = self._build_session(user, client_scope, now, rotated_from_id)
        self.repo.save_grant(grant)
        self.repo.save_session(session)
        return session, grant

    def _result(self, user: UserAccount, session: AuthSession, grant: RefreshGrant, set_cookies: tuple[str, ...] = ()) -> AuthSessionResult:
        workspace = self.workspace.resolve_current_workspace(user.user_id) if self.workspace is not None else None
        return AuthSessionResult(
            user=UserSummary(
                user_id=user.user_id,
                email=user.email,
                email_verified=user.email_verified,
                username=user.username,
            ),
            session=SessionSummary(
                authenticated=True,
                access_expires_at=session.expires_at,
                refresh_expires_at=grant.expires_at,
            ),
            set_cookies=set_cookies,
            workspace=workspace,
        )

    def send_code(self, email: str) -> CodeAccepted:
        email = normalize_email(email)
        now = self.clock.now()

        existing = self.repo.get_user_by_email(email)
        if existing is not None:
            self._audit(
                AuditEventType.REGISTER_FAILED,
                outcome_code="email_already_registered",
                message="邮箱已注册，不能重复进入注册流程",
                user_id=existing.user_id,
                email=email,
            )
            raise EmailAlreadyRegisteredError("邮箱已注册，请完成既有注册流程或直接登录")

        challenge = self.repo.get_active_challenge(email, REGISTER_PURPOSE)
        decision = self.rate_limit.evaluate(challenge, now)
        if not decision.allowed:
            self._audit(
                AuditEventType.CODE_RATE_LIMITED,
                outcome_code="rate_limited",
                message=f"发送过于频繁，请在 {decision.retry_after_seconds} 秒后重试",
                email=email,
            )
            raise RateLimitedError(
                f"发送过于频繁，请在 {decision.retry_after_seconds} 秒后重试",
                decision.retry_after_seconds,
            )

        window_started_at = now
        window_send_count = 1
        if challenge is not None:
            window_elapsed = (now - challenge.window_started_at).total_seconds()
            if window_elapsed < self.rate_limit.window_seconds:
                window_started_at = challenge.window_started_at
                window_send_count = challenge.window_send_count + 1
            challenge.invalidate(now)
            self.repo.save_challenge(challenge)

        code = generate_verification_code()
        new_challenge = EmailVerificationChallenge(
            challenge_id=str(uuid4()),
            email=email,
            purpose=REGISTER_PURPOSE,
            code_digest=code_digest(email, code),
            expires_at=now + timedelta(seconds=self.code_ttl_seconds),
            sent_at=now,
            created_at=now,
            window_started_at=window_started_at,
            window_send_count=window_send_count,
        )
        self.repo.save_challenge(new_challenge)

        # 临时开关（AUTH_SKIP_CODE_VERIFICATION=true）：不实际发信，注册时任意验证码即可通过。
        # 日志只记录事件与计数，不输出验证码本身。
        if self.skip_code_verification:
            if self.logger is not None:
                self.logger.debug("验证码发送已跳过（本地开关 AUTH_SKIP_CODE_VERIFICATION）")
            return CodeAccepted(retry_after_seconds=self.rate_limit.min_interval_seconds, expires_in_seconds=self.code_ttl_seconds)

        try:
            self.sender.send(email, code, self.code_ttl_seconds)
        except Exception as exc:
            self._audit(
                AuditEventType.CODE_SENT,
                outcome_code="send_failed",
                message=f"验证码邮件发送失败：{exc}",
                email=email,
            )
            raise

        self._audit(
            AuditEventType.CODE_SENT,
            outcome_code="accepted",
            message=f"验证码已发送至 {email}",
            email=email,
        )
        return CodeAccepted(retry_after_seconds=self.rate_limit.min_interval_seconds, expires_in_seconds=self.code_ttl_seconds)

    def register(self, email: str, code: str, password: str) -> AuthSessionResult:
        email = normalize_email(email)
        now = self.clock.now()

        policy_failure = check_password_policy(password)
        if policy_failure is not None:
            self._audit(AuditEventType.REGISTER_FAILED, outcome_code="password_policy", message=policy_failure, email=email)
            raise PasswordPolicyError(policy_failure)

        existing = self.repo.get_user_by_email(email)
        if existing is not None:
            self._audit(
                AuditEventType.REGISTER_FAILED,
                outcome_code="email_already_registered",
                message="邮箱已注册，不能重复创建账号",
                user_id=existing.user_id,
                email=email,
            )
            raise EmailAlreadyRegisteredError("邮箱已注册，请直接登录")

        # 临时开关（AUTH_SKIP_CODE_VERIFICATION=true）：跳过验证码校验，便于本地验证注册/登录主流程。
        # 关闭开关后本段逻辑与之前完全一致；上线前必须恢复为始终校验。
        if self.skip_code_verification:
            if self.logger is not None:
                self.logger.debug("验证码校验已跳过（本地开关 AUTH_SKIP_CODE_VERIFICATION）")
        else:
            challenge = self.repo.get_active_challenge(email, REGISTER_PURPOSE)
            if challenge is None or not challenge.is_currently_valid(now):
                self._audit(AuditEventType.REGISTER_FAILED, outcome_code="code_invalid", message="验证码不存在、已过期或不可用", email=email)
                raise InvalidCodeError("验证码不存在、已过期或不可用")

            challenge.record_attempt(now)
            if challenge.state.value == "attempts_exhausted":
                self.repo.save_challenge(challenge)
                self._audit(AuditEventType.REGISTER_FAILED, outcome_code="attempts_exhausted", message="验证码校验尝试次数已用尽", email=email)
                raise InvalidCodeError("验证码校验尝试次数已用尽")

            if code_digest(email, code) != challenge.code_digest:
                self.repo.save_challenge(challenge)
                self._audit(AuditEventType.REGISTER_FAILED, outcome_code="code_mismatch", message="验证码不正确", email=email)
                raise InvalidCodeError("验证码不正确")

            challenge.mark_used(now)
            self.repo.save_challenge(challenge)

        digest, version = self.hasher.hash(password)
        user = UserAccount(
            user_id=str(uuid4()),
            email=email,
            username=username_from_email(email),
            password_hash=digest,
            password_hash_version=version,
            created_at=now,
            updated_at=now,
        )
        user.mark_verified(now)

        if self.workspace is None:
            self.repo.save_user(user)
        else:
            try:
                with self.repo.unit_of_work() as uow:
                    self.repo.save_user(user, uow)
                    self.workspace.create_default_workspace(user, now, uow)
            except Exception as exc:
                self._audit(
                    AuditEventType.REGISTER_FAILED,
                    outcome_code="workspace_creation_failed",
                    message=f"默认工作空间创建失败，注册写入已回滚：{exc}",
                    email=email,
                )
                if self.logger is not None:
                    self.logger.error(f"默认工作空间创建失败：user={user.user_id} 注册回滚；{exc}")
                raise WorkspaceCreationError("默认工作空间创建失败，注册已回滚，请重试") from exc

        client_scope = secrets.token_urlsafe(16)
        session, grant = self._issue_session(user, client_scope, now)
        self._audit(
            AuditEventType.REGISTER_SUCCEEDED,
            outcome_code="accepted",
            message=f"注册成功并自动建立登录状态：{email}",
            user_id=user.user_id,
            email=email,
            client_scope=client_scope,
        )
        set_cookies = self.cookies.issue(
            session.session_id, grant.refresh_grant_id, self.access_ttl_seconds, self.refresh_ttl_seconds
        )
        return self._result(user, session, grant, set_cookies)

    def login(self, email: str, password: str) -> AuthSessionResult:
        email = normalize_email(email)
        now = self.clock.now()

        user = self.repo.get_user_by_email(email)
        if user is None or not user.email_verified:
            self._audit(AuditEventType.LOGIN_FAILED, outcome_code="invalid_credentials", message="邮箱不存在、未验证或密码错误", email=email)
            raise UnauthorizedError("邮箱不存在、未验证或密码错误")

        if not self.hasher.verify(password, user.password_hash):
            self._audit(
                AuditEventType.LOGIN_FAILED,
                outcome_code="invalid_credentials",
                message="邮箱不存在、未验证或密码错误",
                user_id=user.user_id,
                email=email,
            )
            raise UnauthorizedError("邮箱不存在、未验证或密码错误")

        user.mark_login(now)
        self.repo.save_user(user)

        client_scope = secrets.token_urlsafe(16)
        session, grant = self._issue_session(user, client_scope, now)
        self._audit(
            AuditEventType.LOGIN_SUCCEEDED,
            outcome_code="accepted",
            message=f"登录成功：{email}",
            user_id=user.user_id,
            email=email,
            client_scope=client_scope,
        )
        set_cookies = self.cookies.issue(
            session.session_id, grant.refresh_grant_id, self.access_ttl_seconds, self.refresh_ttl_seconds
        )
        return self._result(user, session, grant, set_cookies)

    def current_session(self, session_id: str | None) -> AuthSessionResult:
        now = self.clock.now()
        if not session_id:
            raise UnauthorizedError("当前浏览器没有有效会话，请重新登录")

        session = self.repo.get_session(session_id)
        if session is None or not session.is_valid(now):
            raise UnauthorizedError("当前浏览器没有有效会话，请重新登录")

        session.mark_seen(now)
        self.repo.save_session(session)

        user = self.repo.get_user_by_email_or_id(session.user_id)
        grant = self.repo.get_grant(session.refresh_grant_id)
        if user is None or grant is None:
            raise UnauthorizedError("当前浏览器没有有效会话，请重新登录")

        return self._result(user, session, grant)

    def refresh(self, grant_id: str | None) -> AuthSessionResult:
        now = self.clock.now()
        if not grant_id:
            raise UnauthorizedError("刷新资格不存在或已失效，请重新登录")

        grant = self.repo.get_grant(grant_id)
        if grant is None or not grant.is_valid(now):
            self._audit(AuditEventType.REFRESH_FAILED, outcome_code="grant_invalid", message="刷新资格不存在、已失效、已撤销或已被替换", user_id=grant.user_id if grant else None)
            raise UnauthorizedError("刷新资格不存在或已失效，请重新登录")

        user = self.repo.get_user_by_email_or_id(grant.user_id)
        if user is None:
            self._audit(AuditEventType.REFRESH_FAILED, outcome_code="user_missing", message="刷新资格关联用户不存在", user_id=grant.user_id)
            raise UnauthorizedError("刷新资格不存在或已失效，请重新登录")

        old_session = self.repo.get_session_by_grant(grant.refresh_grant_id)
        if old_session is not None and old_session.state.value == "active":
            old_session.replace(now)

        session, new_grant = self._build_session(user, grant.client_scope, now, rotated_from_id=grant.refresh_grant_id)
        grant.rotate_to(new_grant.refresh_grant_id, now)
        self.repo.rotate_session(grant, old_session, new_grant, session)
        self._audit(
            AuditEventType.REFRESH_SUCCEEDED,
            outcome_code="accepted",
            message=f"刷新成功，旧刷新资格已失效：{user.email}",
            user_id=user.user_id,
            email=user.email,
            client_scope=grant.client_scope,
        )
        set_cookies = self.cookies.issue(
            session.session_id, new_grant.refresh_grant_id, self.access_ttl_seconds, self.refresh_ttl_seconds
        )
        return self._result(user, session, new_grant, set_cookies)

    def logout(self, session_id: str | None, grant_id: str | None) -> None:
        now = self.clock.now()
        if not session_id:
            raise UnauthorizedError("当前浏览器没有可退出的登录状态")

        session = self.repo.get_session(session_id)
        if session is None or not session.is_valid(now):
            self._audit(AuditEventType.LOGOUT_FAILED, outcome_code="session_invalid", message="退出失败：当前会话已失效", email=None)
            raise UnauthorizedError("当前浏览器没有可退出的登录状态")

        grant = self.repo.get_grant(session.refresh_grant_id)
        if grant is not None and grant.state.value == "active":
            grant.revoke(now)
            self.repo.save_grant(grant)

        session.revoke(now)
        self.repo.save_session(session)

        user = self.repo.get_user_by_email_or_id(session.user_id)
        self._audit(
            AuditEventType.LOGOUT_SUCCEEDED,
            outcome_code="accepted",
            message="当前浏览器当前会话已退出",
            user_id=session.user_id,
            email=user.email if user else None,
            client_scope=session.client_scope,
        )

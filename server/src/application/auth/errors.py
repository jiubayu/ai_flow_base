from __future__ import annotations


class AuthError(Exception):
    code = "auth_error"
    status = 400

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class RateLimitedError(AuthError):
    code = "rate_limited"
    status = 429

    def __init__(self, message: str, retry_after_seconds: int) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class EmailUnavailableError(AuthError):
    code = "email_unavailable"
    status = 503


class InvalidCodeError(AuthError):
    code = "invalid_code"
    status = 400


class PasswordPolicyError(AuthError):
    code = "password_policy"
    status = 400


class EmailAlreadyRegisteredError(AuthError):
    code = "email_already_registered"
    status = 409


class UnauthorizedError(AuthError):
    code = "unauthorized"
    status = 401

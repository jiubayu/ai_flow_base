from __future__ import annotations


class WorkspaceError(Exception):
    code = "workspace_error"
    status = 400

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class WorkspaceAccessDeniedError(WorkspaceError):
    code = "WORKSPACE_ACCESS_DENIED"
    status = 403


class WorkspaceNotFoundError(WorkspaceError):
    code = "WORKSPACE_NOT_FOUND"
    status = 404


class WorkspaceCurrentMissingError(WorkspaceError):
    code = "WORKSPACE_CURRENT_MISSING"
    status = 400


class WorkspaceManagerRequiredError(WorkspaceError):
    code = "WORKSPACE_MANAGER_REQUIRED"
    status = 403


class UserNotFoundError(WorkspaceError):
    code = "USER_NOT_FOUND"
    status = 404


class WorkspaceMemberAlreadyExistsError(WorkspaceError):
    code = "WORKSPACE_MEMBER_ALREADY_EXISTS"
    status = 409


class WorkspaceMemberNotFoundError(WorkspaceError):
    code = "WORKSPACE_MEMBER_NOT_FOUND"
    status = 404


class WorkspaceLastManagerProtectedError(WorkspaceError):
    code = "WORKSPACE_LAST_MANAGER_PROTECTED"
    status = 409


class WorkspaceRoleInvalidError(WorkspaceError):
    code = "WORKSPACE_ROLE_INVALID"
    status = 422


class WorkspaceCreationError(WorkspaceError):
    code = "WORKSPACE_CREATION_FAILED"
    status = 500


class ApplicationNameInvalidError(WorkspaceError):
    code = "APPLICATION_NAME_INVALID"
    status = 400


class ApplicationDescriptionInvalidError(WorkspaceError):
    code = "APPLICATION_DESCRIPTION_INVALID"
    status = 400


class ApplicationNameDuplicatedError(WorkspaceError):
    code = "APPLICATION_NAME_DUPLICATED"
    status = 409


class ApplicationNotFoundError(WorkspaceError):
    code = "APPLICATION_NOT_FOUND"
    status = 404


class WorkspaceSessionMissingError(WorkspaceError):
    code = "AUTH_SESSION_MISSING"
    status = 401


class WorkspaceSessionExpiredError(WorkspaceError):
    code = "AUTH_SESSION_EXPIRED"
    status = 401

from __future__ import annotations

import re
from enum import Enum


class WorkspaceRole(Enum):
    MANAGER = "manager"
    MEMBER = "member"


class MembershipStatus(Enum):
    ACTIVE = "active"
    REMOVED = "removed"


class WorkspaceStatus(Enum):
    ACTIVE = "active"


class WorkspaceEventType(Enum):
    WORKSPACE_CREATED = "workspace_created"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    MEMBER_ROLE_CHANGED = "member_role_changed"
    WORKSPACE_SWITCHED = "workspace_switched"
    WORKSPACE_ACCESS_DENIED = "workspace_access_denied"
    APPLICATION_CREATED = "application_created"
    APPLICATION_UPDATED = "application_updated"


class ApplicationStatus(Enum):
    DRAFT = "draft"


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")


def normalize_username(username: str) -> str:
    return username.strip().lower()


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.fullmatch(username))


def username_from_email(email: str) -> str:
    return normalize_username(email.split("@", 1)[0])


def normalize_workspace_name(name: str) -> str:
    return name.strip()


def is_valid_workspace_name(name: str) -> bool:
    return bool(name.strip())


def default_workspace_name(username: str) -> str:
    return f"{username} 的工作空间"


def is_valid_role(role: str) -> bool:
    return role in {item.value for item in WorkspaceRole}


APPLICATION_NAME_MIN_LENGTH = 1
APPLICATION_NAME_MAX_LENGTH = 80
APPLICATION_DESCRIPTION_MAX_LENGTH = 500


def normalize_application_name(name: str) -> str:
    return name.strip()


def normalize_application_description(description: str) -> str:
    return description.strip()


def is_valid_application_name(name: str) -> bool:
    stripped = name.strip()
    return APPLICATION_NAME_MIN_LENGTH <= len(stripped) <= APPLICATION_NAME_MAX_LENGTH


def is_valid_application_description(description: str) -> bool:
    return len(description.strip()) <= APPLICATION_DESCRIPTION_MAX_LENGTH

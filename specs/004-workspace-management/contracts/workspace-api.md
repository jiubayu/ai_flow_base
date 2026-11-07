# API Contract: 工作空间与成员管理

## Common Error Shape

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "用户可理解的错误说明"
  }
}
```

## Shared Types

### WorkspaceSummary

```json
{
  "workspace_id": "uuid",
  "name": "alice 的工作空间",
  "role": "manager",
  "is_current": true
}
```

`role`: `manager` 或 `member`。

### WorkspaceMember

```json
{
  "user_id": "uuid",
  "username": "alice",
  "role": "manager",
  "joined_at": "2026-05-20T10:00:00+00:00"
}
```

## Auth Session Response Extension

Existing endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/session`
- `POST /api/auth/refresh`

Response MUST include workspace context:

```json
{
  "user": {
    "user_id": "uuid",
    "username": "alice"
  },
  "session": {
    "authenticated": true,
    "access_expires_at": "2026-05-20T10:15:00+00:00",
    "refresh_expires_at": "2026-05-27T10:00:00+00:00"
  },
  "workspace": {
    "current": {
      "workspace_id": "uuid",
      "name": "alice 的工作空间",
      "role": "manager",
      "is_current": true
    },
    "available": [
      {
        "workspace_id": "uuid",
        "name": "alice 的工作空间",
        "role": "manager",
        "is_current": true
      }
    ]
  }
}
```

If user has no available workspace:

```json
{
  "workspace": {
    "current": null,
    "available": []
  }
}
```

## GET /api/workspaces

List current user's accessible workspaces.

**Auth**: Required browser session.

**Response 200**:

```json
{
  "workspaces": [
    {
      "workspace_id": "uuid",
      "name": "alice 的工作空间",
      "role": "manager",
      "is_current": true
    }
  ]
}
```

**Errors**:

- `401 AUTH_SESSION_MISSING`
- `401 AUTH_SESSION_EXPIRED`

## POST /api/workspaces/current

Switch current workspace.

**Auth**: Required browser session.

**Request**:

```json
{
  "workspace_id": "uuid"
}
```

**Response 200**:

```json
{
  "current": {
    "workspace_id": "uuid",
    "name": "team workspace",
    "role": "member",
    "is_current": true
  },
  "available": [
    {
      "workspace_id": "uuid",
      "name": "team workspace",
      "role": "member",
      "is_current": true
    }
  ]
}
```

**Errors**:

- `403 WORKSPACE_ACCESS_DENIED`: 用户不是目标工作空间 active 成员。
- `404 WORKSPACE_NOT_FOUND`: 工作空间不存在或不可访问。

## GET /api/workspaces/current/members

List members in current workspace.

**Auth**: Required browser session and current workspace.

**Response 200**:

```json
{
  "members": [
    {
      "user_id": "uuid",
      "username": "alice",
      "role": "manager",
      "joined_at": "2026-05-20T10:00:00+00:00"
    }
  ]
}
```

**Errors**:

- `400 WORKSPACE_CURRENT_MISSING`: 用户没有当前工作空间。
- `403 WORKSPACE_ACCESS_DENIED`

## POST /api/workspaces/current/members

Add an already registered user to current workspace by username.

**Auth**: Current workspace role must be `manager`.

**Request**:

```json
{
  "username": "bob",
  "role": "member"
}
```

**Response 201**:

```json
{
  "member": {
    "user_id": "uuid",
    "username": "bob",
    "role": "member",
    "joined_at": "2026-05-20T10:05:00+00:00"
  }
}
```

**Errors**:

- `403 WORKSPACE_MANAGER_REQUIRED`: 当前用户不是管理者。
- `404 USER_NOT_FOUND`: 用户名不存在。
- `409 WORKSPACE_MEMBER_ALREADY_EXISTS`: 用户已是当前工作空间 active 成员。
- `422 WORKSPACE_ROLE_INVALID`: 角色不是 `manager` 或 `member`。

## PATCH /api/workspaces/current/members/{user_id}

Change member role in current workspace.

**Auth**: Current workspace role must be `manager`.

**Request**:

```json
{
  "role": "manager"
}
```

**Response 200**:

```json
{
  "member": {
    "user_id": "uuid",
    "username": "bob",
    "role": "manager",
    "joined_at": "2026-05-20T10:05:00+00:00"
  }
}
```

**Errors**:

- `403 WORKSPACE_MANAGER_REQUIRED`
- `404 WORKSPACE_MEMBER_NOT_FOUND`
- `409 WORKSPACE_LAST_MANAGER_PROTECTED`: 不能让工作空间失去最后一个管理者。
- `422 WORKSPACE_ROLE_INVALID`

## DELETE /api/workspaces/current/members/{user_id}

Remove member from current workspace. This does not delete the user account.

**Auth**: Current workspace role must be `manager`.

**Response 204**: Empty body.

**Errors**:

- `403 WORKSPACE_MANAGER_REQUIRED`
- `404 WORKSPACE_MEMBER_NOT_FOUND`
- `409 WORKSPACE_LAST_MANAGER_PROTECTED`: 不能删除最后一个管理者。

## Logging Requirements

- Successful member add/remove/role change: info log with actor user, target user, workspace id, result code.
- Access denied and last manager protection: warning log with actor user, workspace id, result code.
- Migration and default workspace creation failure: error log with user id and operation, without password, token, secret or full connection string.

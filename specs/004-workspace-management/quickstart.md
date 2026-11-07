# Quickstart: 工作空间与成员管理

## Preconditions

- 当前分支：`004-workspace-management`
- 后端虚拟环境和前端依赖已按项目 README 安装。
- 不新增第三方依赖。
- 开发环境日志级别开启 debug，后端日志写入 `server/logs/backend.log`。

## Backend Migration Validation

1. 运行迁移：

```bash
cd server
uv run python scripts/migrate_auth_schema.py
```

2. 验证 schema 和存量回填：

```bash
cd server
uv run python - <<'PY'
import sqlite3
from src.core.config import get_settings

db = get_settings().result_store_path
with sqlite3.connect(db) as con:
    for table in ["workspaces", "workspace_memberships", "user_workspace_preferences", "workspace_audit_events"]:
        row = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        assert row is not None, table
    missing_workspace = con.execute("""
        SELECT COUNT(*) FROM user_accounts
        WHERE user_id NOT IN (
            SELECT user_id FROM workspace_memberships WHERE status = 'active'
        )
    """).fetchone()[0]
    assert missing_workspace == 0, missing_workspace
print("workspace migration verified")
PY
```

## Backend Tests

Run targeted tests:

```bash
cd server
uv run pytest tests/contract/test_auth_api.py tests/contract/test_workspace_api.py tests/integration/test_workspace_flow.py tests/unit/workspace
```

Expected coverage:

- Registration returns default workspace and manager role.
- Existing user migration creates default workspace and manager membership.
- Current workspace preference persists and falls back when access is removed.
- Manager can add member by username.
- Manager can remove member.
- Manager can change role.
- Last manager cannot be removed or downgraded.
- Member cannot manage members.
- Unauthorized workspace access returns explicit error code.
- Audit events are recorded for member management and protected failures.

## Backend Service Manual Verification

1. Start backend:

```bash
cd server
uv run python -m uvicorn src.main:app --reload --port 8000
```

2. Register a user and confirm workspace context:

```bash
curl -i -c /tmp/ai-flow-a.cookies \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice_ws","password":"abc12345"}' \
  http://127.0.0.1:8000/api/auth/register
```

Expected response includes `workspace.current.role = "manager"` and one available workspace.

3. Register second user:

```bash
curl -i -c /tmp/ai-flow-b.cookies \
  -H 'Content-Type: application/json' \
  -d '{"username":"bob_ws","password":"abc12345"}' \
  http://127.0.0.1:8000/api/auth/register
```

4. Add second user to first user's workspace:

```bash
curl -i -b /tmp/ai-flow-a.cookies \
  -H 'Content-Type: application/json' \
  -d '{"username":"bob_ws","role":"member"}' \
  http://127.0.0.1:8000/api/workspaces/current/members
```

Expected status: `201`.

5. Verify ordinary member cannot manage members:

```bash
curl -i -b /tmp/ai-flow-b.cookies \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice_ws","role":"member"}' \
  http://127.0.0.1:8000/api/workspaces/current/members
```

Expected status: `403` with `WORKSPACE_MANAGER_REQUIRED`.

6. Inspect backend logs:

```bash
tail -n 200 server/logs/backend.log
```

Expected log evidence includes workspace creation, member add, permission denial, and no sensitive values.

## Frontend Validation

1. Run typecheck:

```bash
cd ui
pnpm run typecheck
```

2. Start frontend:

```bash
cd ui
pnpm run dev
```

3. Manual checks:

- Register a user and confirm current workspace is shown.
- Register or login another user and add it by username from a manager session.
- Switch workspaces when the user belongs to multiple workspaces.
- Confirm ordinary member cannot see or execute member management controls.
- Confirm browser console has no runtime errors.

## Data Upgrade Release Notes

- Back up SQLite database before migration.
- Deploy compatible code that can read users with and without workspace preference during migration.
- Run migration and validation before enabling member management UI.
- If validation fails before release, restore backup and keep old application version.
- Do not tighten non-null constraints on business data `workspace_id` until all read/write paths are workspace scoped and validation confirms no null values remain.

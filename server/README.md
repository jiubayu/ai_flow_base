# server：FastAPI 后端

分层架构，入口为 `src/main.py`（`create_app()`），Celery 入口为 `src/celery_app.py`。

## 启动

```bash
uv sync
cp .env.example .env   # 必填项缺失时启动会显式失败
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000
uv run celery -A src.celery_app:app worker -l info
```

## 认证（邮箱验证码与密码）

```bash
uv run python scripts/migrate_auth_schema.py   # 幂等迁移；认证表与结果库共用同一 SQLite 文件
```

- `.env` 需补齐 `AUTH_ACCESS_TTL_MINUTES`、`AUTH_REFRESH_TTL_DAYS`、`AUTH_CODE_TTL_MINUTES`、限流参数与 `SMTP_*` 配置；SMTP 缺失时发送验证码接口显式失败（503），不静默兜底。
- 会话通过 HttpOnly Cookie 下发（`access_session` / `refresh_grant`）；`AUTH_COOKIE_SECURE` 必须与本地协议一致，CORS `allow_credentials` 与 `FRONTEND_ORIGIN` 必须匹配，否则浏览器不会附带 Cookie。
- 刷新为一次性轮换：旧 refresh 资格用后即失效；登出仅撤销当前浏览器会话，不影响其他浏览器。
- 完整验收步骤见 [specs/003-email-password-auth/quickstart.md](../specs/003-email-password-auth/quickstart.md)。

## 工作空间与成员管理

```bash
uv run python scripts/migrate_auth_schema.py   # 同一脚本幂等执行认证 + 工作空间迁移
```

- 工作空间表（`workspaces`、`workspace_memberships`、`workspace_memberships_history`、`workspace_audit_events`）与认证表共用同一 SQLite 文件；迁移幂等，`user_accounts.username` 列缺失时自动补齐并回填历史数据。
- 活跃成员唯一性由部分唯一索引 `ux_memberships_active` 保证；历史表记录成员角色与状态变更，审计事件按工作空间记录操作。
- 业务规则：角色仅 `manager` / `member`；最后一个管理者不可降级或移除（last-manager 保护）；成员被移除后重新加入会生成新的活跃成员记录。
- 当前工作空间按用户偏好（preference）恢复；偏好失效时回落到用户可访问的第一个工作空间。
- 契约测试与逐条验收步骤见 [specs/004-workspace-management/quickstart.md](../specs/004-workspace-management/quickstart.md)。

## 应用工作空间（005）

```bash
uv run python scripts/migrate_workspace_schema.py   # 幂等迁移 + schema 校验输出
```

- 迁移覆盖 `workspaces`、`workspace_memberships`、`user_workspace_preferences`、`workspace_audit_events` 与 `workspace_applications`；重复执行安全，校验结果按表输出缺失项（缺失时脚本以非零码退出）。
- `workspace_applications` 的名称唯一性由唯一索引 `ux_workspace_applications_name`（`workspace_id, name`）保证；卡片列表按 `ix_workspace_applications_workspace`（`workspace_id, updated_at`）读取。
- 应用只有名称与描述可编辑，首版没有删除能力；名称 1-80 个非空白字符、描述 0-500 字符，重复名称返回 409。
- 身份一律来自会话 Cookie（`GET /api/workspace/current`、`POST|GET|PATCH /api/workspace/applications*`），不接受客户端传入的 `user_id`。
- 数据流日志为 debug 级：概览读取、详情读取、名称重复拒绝只记录 user/workspace/application id 与计数，不含 Cookie、密码或其他敏感值。
- 验收步骤见 [specs/005-app-workspace-canvas/quickstart.md](../specs/005-app-workspace-canvas/quickstart.md)。

## 测试

```bash
pytest
```

- `tests/contract/`：bootstrap、认证 API 与工作空间 API 契约测试
- `tests/integration/`：后端→Celery 任务链路、devctl 脚本生命周期与失败路径、认证注册/登录/刷新/登出全链路、工作空间切换与成员管理全链路
- `tests/unit/`：配置解析、结果存储边界，认证密码散列、验证码限流、刷新轮换，以及工作空间角色与 last-manager 保护规则用例

工作空间相关测试可单独运行：

```bash
uv run pytest tests/contract/test_auth_api.py tests/contract/test_workspace_api.py tests/integration/test_workspace_flow.py tests/unit/workspace
```

## 新增代码放在哪里

| 内容 | 层 | 示例 |
|---|---|---|
| 业务规则、实体、状态机 | `src/domain/` | `domain/bootstrap/entities.py` |
| 用例编排、应用服务 | `src/application/` | `application/bootstrap/use_cases.py` |
| broker、持久化、日志实现 | `src/infrastructure/` | `infrastructure/celery/tasks.py` |
| HTTP 路由与错误映射 | `src/presentation/api/` | `presentation/api/health.py` |
| 配置与日志引导 | `src/core/` | `core/config.py` |

依赖方向：presentation → application → domain；infrastructure 实现 domain 需要的能力，`core` 被所有层使用但不反向依赖业务层。逐层说明见 [src/README.md](src/README.md)。

## 运行产物

- 日志：`logs/`（由 devctl 或应用写入）
- 运行状态：`.runtime/`（PID、Celery 队列、SQLite 结果库）

两者均不入库，仅保留 `.gitkeep` 占位。

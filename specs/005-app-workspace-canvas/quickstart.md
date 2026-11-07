# 快速开始：应用工作空间与编排画布

## 目标

在 `005-app-workspace-canvas` worktree 中完成实现后的迁移、启动与验证，确认登录用户默认进入自己的工作空间，能够创建多个应用、以卡片查看应用、进入应用详情、编辑应用名称和说明，并看到首版空编排画布入口。

## 前置条件

- 已安装 Python 3.11、`uv`、Node.js 20+、`pnpm`
- 当前目录位于 `/home/xmin/workspace/code/ai-flow/.worktrees/005-app-workspace-canvas`
- 已在 `server/` 和 `ui/` 安装依赖
- 已完成邮箱验证码与密码认证功能，可注册/登录并持有浏览器 Cookie 会话
- 后续实现、测试和验证均在当前 worktree 内执行

## 1. 配置后端环境

在 `server/.env` 中确认以下配置：

- `APP_DEBUG=true`
- `FRONTEND_ORIGIN=http://127.0.0.1:5173`
- `RESULT_DB_PATH=.runtime/demo-tasks.sqlite3`
- 认证功能所需 Cookie 与 SMTP 配置已按认证 quickstart 配好

说明：

- 工作空间表复用 `RESULT_DB_PATH` 指向的 SQLite 文件。
- debug 日志应能观察工作空间自动创建、应用创建、应用编辑和权限拒绝路径。

## 2. 执行工作空间数据库迁移

```bash
cd server
uv run python scripts/migrate_workspace_schema.py
```

预期结果：

- `workspaces` 和 `workspace_applications` 表创建成功
- 默认工作空间唯一约束和应用名称唯一约束创建成功
- 重复执行迁移不会因对象已存在而失败

## 3. 启动后端

```bash
cd server
uv run python -m uvicorn src.main:app --reload --port 8000
```

预期结果：

- 后端成功启动
- `server/logs/backend.log` 中可看到工作空间路由和迁移相关上下文

## 4. 启动前端

```bash
cd ui
pnpm run dev
```

预期结果：

- 浏览器可打开 `http://127.0.0.1:5173`（devctl 启动时按 `FRONTEND_PORT` 传入 `--port`，当前为 5174；`server/.env` 的 `FRONTEND_ORIGIN` 必须与之一致，否则浏览器不会附带会话 Cookie）
- 每个页面一条路由（react-router-dom）：`/` 按登录状态分流，`/auth` 认证入口，`/workspace` 应用卡片列表，`/workspace/applications/:applicationId` 应用详情，`/session` 会话与工作空间切换，`/theme`、`/bootstrap` 公开页
- 未登录时展示认证入口；未登录直接访问 `/workspace` 或 `/workspace/applications/:id` 时回到 `/auth`
- 登录后默认进入个人工作空间页面（`/workspace`）

## 5. 验证默认工作空间自动创建

1. 使用一个新账号完成注册或登录。
2. 打开前端应用或请求当前工作空间接口。
3. 查询 SQLite 数据库中的 `workspaces` 表。

预期结果：

- 首次访问后自动创建 1 个个人默认工作空间。
- 前端展示该工作空间，不要求用户手动创建。
- 重复刷新页面不会创建重复默认工作空间。

## 6. 验证应用创建和卡片列表

1. 在空工作空间中创建应用，填写应用名称和说明。
2. 确认应用卡片出现在列表中。
3. 连续创建多个不同名称应用。
4. 尝试创建同名应用。

预期结果：

- 每个不同名称应用以独立卡片展示。
- 卡片包含名称、说明或状态、最近更新时间和进入入口。
- 同一工作空间内同名应用被拒绝，并提示应用名称已存在。

## 7. 验证应用详情和编辑

1. 从应用卡片进入应用详情（地址为 `/workspace/applications/:applicationId`）。
2. 确认左侧展示应用名称、说明、状态和更新时间。
3. 编辑应用名称和说明并保存。
4. 返回工作空间列表（「返回应用列表」是真实链接）。

预期结果：

- 详情页由 URL 参数决定应用：刷新页面、浏览器后退或直接输入地址都落到同一应用。
- 详情页左侧应用信息和右侧画布区域同时可见。
- 保存后详情页和工作空间卡片展示一致的最新名称与说明。
- 编辑名称为同一工作空间内已有名称时被拒绝。
- 页面不提供删除应用入口。

## 8. 验证首版编排画布

1. 进入任一应用详情。
2. 查看右侧编排画布区域。
3. 尝试寻找节点新增、移动、连接、删除、保存或运行入口。

预期结果：

- 画布区域显示空画布状态和“开始编排”入口。
- 不存在节点编辑、流程保存、运行或调试能力。
- 空画布状态不会被误解为加载失败。

## 9. 验证权限隔离

1. 使用用户 A 创建应用。
2. 使用用户 B 登录并进入工作空间。
3. 尝试通过用户 A 的应用 ID 请求详情或编辑。

预期结果：

- 用户 B 看不到用户 A 的应用卡片。
- 用户 B 不能读取或修改用户 A 的应用。
- 后端返回明确错误语义，且不泄漏受保护应用内容。

## 10. 执行自动化验证

```bash
cd server
uv run pytest tests/contract/test_workspace_api.py tests/integration/test_workspace_flow.py
uv run pytest tests/unit/workspace

cd ../ui
pnpm run typecheck
pnpm run build
```

预期结果：

- 工作空间 API 契约测试通过。
- 默认工作空间、应用创建、重名拒绝、编辑、权限隔离集成测试通过。
- 工作空间领域和值对象单元测试通过。
- 前端类型检查和构建通过。

## 11. 检查日志与数据库状态

- 查看 `server/logs/backend.log`，确认存在以下 debug 级上下文：
  - 默认工作空间自动创建或复用
  - 应用创建成功
  - 应用名称/说明编辑成功
  - 重名拒绝
  - 无权访问拒绝
- 查询 SQLite 数据库，确认：
  - 每个用户只有 1 个默认工作空间
  - 同一工作空间内应用名称唯一
  - 不同用户工作空间可以存在同名应用
  - 应用编辑后 `updated_at` 更新

## 12. 失败恢复

- 若迁移失败，先停止后端进程，再恢复迁移前数据库备份或手动移除未完成的新表。
- 若登录后未进入工作空间，优先检查认证 Cookie、`/api/auth/session`、`/api/workspace/current` 和后端日志。
- 若跨用户数据可见，立即停止继续开发并修复权限过滤和测试覆盖。
- 若前端页面空白，检查浏览器控制台、网络请求和 `server/logs/frontend.log`。

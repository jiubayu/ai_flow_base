# 快速开始：邮箱验证码与密码认证

## 目标

在本地 worktree 中完成认证功能实现后的迁移、启动与验证，确认邮箱验证码注册、邮箱密码登录、Cookie 自动携带、会话刷新与当前浏览器登出都按规格工作。

## 前置条件

- 已安装 Python 3.11、`uv`、Node.js 20+、`pnpm`
- 当前目录位于 `003-email-password-auth` worktree
- 已在 `server/` 和 `ui/` 安装依赖
- 已准备可用的 SMTP 配置；若 SMTP 不可用，本特性不应假装发送成功

## 1. 配置后端环境

在 `server/.env` 中补齐以下配置：

- `APP_DEBUG=true`
- `FRONTEND_ORIGIN=http://127.0.0.1:5173`
- `DATABASE_URL=postgresql+psycopg://ai_flow:ai_flow@127.0.0.1:5432/ai_flow`
- `AUTH_ACCESS_TTL_MINUTES`
- `AUTH_REFRESH_TTL_DAYS`
- `AUTH_CODE_TTL_MINUTES`
- `AUTH_CODE_MIN_INTERVAL_SECONDS`
- `AUTH_CODE_WINDOW_SECONDS`
- `AUTH_CODE_WINDOW_LIMIT`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_ADDRESS`
- `AUTH_COOKIE_SECURE`

说明：

- 本地开发可把 access TTL 设为较短值，便于验证刷新链路。
- 认证表位于 PostgreSQL（pgvector）schema，由 `scripts/migrate_postgres_schema.py` 初始化；旧 SQLite 数据文件不迁移、不读取。

## 2. 执行认证数据库迁移

```bash
cd server
uv run python scripts/migrate_postgres_schema.py
```

预期结果：

- 认证相关表与索引创建成功
- 重复执行不会报重复建表错误
- 控制台输出迁移结果，后端日志中可看到迁移上下文

## 3. 启动后端

```bash
cd server
uv run python -m uvicorn src.main:app --reload --port 8000
```

预期结果：

- 后端成功启动
- `server/logs/backend.log` 中能看到认证配置和路由初始化日志

## 4. 启动前端

```bash
cd ui
pnpm run dev
```

预期结果：

- 浏览器可打开本地前端页面
- 认证表单或认证入口可正常渲染
- 浏览器控制台无跨域、Cookie 或脚本错误

## 5. 验证注册链路

1. 输入一个未注册邮箱并发送验证码。
2. 检查邮箱是否收到验证码邮件。
3. 在 60 秒内再次发送，确认收到明确的限流提示。
4. 使用正确验证码和满足规则的密码提交注册。

预期结果：

- 邮箱收到验证码
- 超频发送被拒绝且返回等待时间
- 注册成功后浏览器自动进入已登录状态，无需再手工登录

## 6. 验证登录、会话与刷新

1. 使用已注册邮箱和密码登录。
2. 刷新页面或访问需要身份识别的后续接口，确认浏览器自动携带 Cookie。
3. 让 access 会话过期，随后触发一次需要身份识别的请求。
4. 确认系统通过刷新资格恢复当前浏览器会话。
5. 点击页面中的“手动刷新会话”，确认会话仍保持可用。

预期结果：

- 登录成功后当前浏览器会话可持续使用
- access 会话过期后无需重新输入邮箱和密码即可刷新恢复
- 刷新成功后旧 refresh 资格不可再次使用

## 7. 验证当前浏览器登出

1. 在当前浏览器执行登出。
2. 继续访问需要身份识别的接口或页面。
3. 若另一个浏览器仍保持登录，确认其会话不受影响。
4. 再次刷新页面，确认当前浏览器不会被恢复为已登录。

预期结果：

- 当前浏览器当前会话立即失效
- 当前浏览器继续访问受保护接口时收到未登录结果
- 其他浏览器的会话保持不变

## 8. 执行自动化验证

```bash
cd server
uv run pytest tests/contract/test_auth_api.py tests/integration/test_auth_flow.py

cd server
uv run pytest tests/unit/auth

cd ../ui
pnpm run typecheck
pnpm run build
```

预期结果：

- 认证接口契约与集成测试通过
- 前端类型检查与构建通过

## 9. 检查日志与数据库状态

- 查看 `server/logs/backend.log`，确认存在验证码发送、登录、刷新、登出等调试日志
- 查询 PostgreSQL 数据库，确认：
  - 用户邮箱已归一化存储
  - 当前浏览器登出后对应会话记录已撤销
  - 刷新成功后旧刷新资格已被标记替换
  - 审计事件已记录关键成功/失败路径

## 10. 失败恢复

- 若迁移失败，先停止后端进程，再根据迁移脚本输出恢复数据库备份或回滚表结构
- 若 SMTP 不可用，先修正 `.env` 中的邮件配置，再重新验证发送链路
- 若 Cookie 未自动携带，优先检查：
  - 前端请求是否启用了 `credentials: "include"`
  - CORS `allow_credentials` 与 `FRONTEND_ORIGIN` 是否匹配
  - `AUTH_COOKIE_SECURE` 是否与本地协议一致

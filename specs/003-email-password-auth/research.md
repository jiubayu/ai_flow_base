# 研究记录：邮箱验证码与密码认证

## 决策 1：浏览器认证采用“服务端持久化会话 + HTTP Only Cookie”而非 JWT

- Decision: 登录成功后签发短期 access 会话和长期 refresh 资格，二者都通过 HTTP Only Cookie 传递，后端持久化会话状态并在每次受保护请求中校验。
- Rationale: 当前项目未引入 JWT 相关依赖，且需求明确要求“浏览器自动带上登录凭证”“过期后支持刷新”“退出登录后彻底失效”。服务端持久化的 opaque session 更容易实现当前浏览器登出失效、刷新轮换和服务端撤销，不需要额外依赖。
- Alternatives considered:
  - JWT access token + refresh token：需要额外签名/校验依赖或自实现复杂签名逻辑，且服务端撤销粒度更复杂。
  - 仅使用单一长会话 Cookie：无法满足过期刷新与安全轮换需求。

## 决策 2：密码散列使用 Python 标准库 `hashlib.scrypt`

- Decision: 使用 `hashlib.scrypt` 生成带随机盐的密码摘要，并保存算法版本、参数与盐值，便于后续渐进升级。
- Rationale: 这是当前依赖边界内最安全、最现实的方案，不需新增 `bcrypt`/`passlib` 等第三方依赖，也比单纯 `pbkdf2_hmac` 更具抗硬件暴力破解能力。
- Alternatives considered:
  - `bcrypt` / `passlib`：安全成熟，但会新增未批准依赖。
  - `pbkdf2_hmac`：无需新依赖，但在相同配置下内存硬化能力较弱。
  - 明文或可逆加密：违反基本安全要求，直接排除。

## 决策 3：验证码模型使用“单邮箱单有效挑战 + 双重发送限流”

- Decision: 同一邮箱在注册场景下任一时刻只保留 1 份有效验证码；新验证码生成后旧验证码立即失效。发送限流同时包含 60 秒最小发送间隔和 15 分钟滚动时间窗内最多 5 次发送。
- Rationale: 这与已确认的澄清结果一致，既能抑制连续点击，也能限制短时间批量滥发；单活验证码可显著降低验证歧义和攻击面。
- Alternatives considered:
  - 仅最小发送间隔：无法限制窗口内持续滥发。
  - 仅固定窗口限流：无法阻止用户在数秒内连续多次点击。
  - 多份验证码并存：会造成验证逻辑复杂且易出错。

## 决策 4：验证码与刷新资格都采用“服务端可撤销状态”

- Decision: 验证码只存储摘要和状态字段，不保存明文；刷新资格采用一次性轮换，刷新成功后立即撤销旧资格并签发新资格。当前浏览器登出时，撤销当前 access 会话与其绑定的 refresh 资格。
- Rationale: 需求强调当前浏览器退出即失效、刷新资格一次性轮换和旧凭证不可复用。服务端可撤销状态最适合支撑这些规则与后续审计。
- Alternatives considered:
  - 仅校验 Cookie 是否存在：无法服务端强制失效，也不满足登出后的安全性。
  - 刷新资格可重复使用直到过期：若资格泄漏，重放风险更高。

## 决策 5：邮件发送通过基础设施层 SMTP 适配器完成，失败时显式报错

- Decision: 在 `infrastructure/messaging` 中实现 SMTP 邮件发送适配器，基于 Python 标准库 `smtplib` 与 `email` 模块发送验证码邮件；配置缺失或发送失败时，接口直接返回明确错误并记录日志。
- Rationale: 认证能力需要真实邮件发送链路，而当前仓库未集成第三方邮件 SDK。SMTP 是最小可行且不新增依赖的方式，也符合“外部服务必须通过基础设施层适配”的架构约束。
- Alternatives considered:
  - 新增第三方邮件服务 SDK：超出当前依赖批准范围。
  - 仅写日志不真正发信：不满足“邮箱验证码”功能目标。
  - 静默降级为假发送成功：违反禁止静默兜底的约束。

## 决策 6：认证表结构通过幂等迁移脚本落地，数据库仍复用当前 SQLite 文件

- Decision: 复用现有 `RESULT_DB_PATH` 指向的 SQLite 文件，在其中新增认证相关表；通过 `server/scripts/migrate_auth_schema.py` 执行幂等迁移，负责建表、索引、唯一约束和必要的兼容检查。
- Rationale: 当前工程已经以 SQLite 作为本地状态持久化入口，复用现有数据库文件可最小化运维复杂度；迁移脚本满足 AGENTS 对 schema 变更必须提供升级路径与验证方式的要求。
- Alternatives considered:
  - 新增第二个专用 SQLite 文件：会让本地运维与配置分裂。
  - 仅依赖运行时 `create_all`：缺乏显式升级/回滚步骤，不符合数据升级规范。
  - 引入 Alembic：需要新增依赖和更多模板配置，超出当前最小实现。

## 决策 7：前端统一通过 `fetch(..., credentials: "include")` 消费认证接口

- Decision: 扩展 `ui/src/shared/lib/http.ts`，让认证相关请求统一携带 `credentials: "include"`，并由 `auth` feature 封装注册、登录、刷新、当前会话查询与登出 API。
- Rationale: 后端已启用 `allow_credentials=True` 的 CORS 中间件，Cookie 会话方案要求浏览器自动附带凭证。统一在共享 HTTP 层处理可避免业务组件各自手写凭证参数。
- Alternatives considered:
  - 每个请求点单独添加 `credentials`：容易遗漏，导致认证行为不一致。
  - 改为 localStorage 保存令牌：不满足 HTTP Only Cookie 的安全目标。

## 决策 8：验证策略以契约测试、集成测试和浏览器真实链路验证三层组合

- Decision: 后端新增认证 API 契约测试和端到端集成测试，覆盖发送验证码、注册、登录、刷新、登出和限流失败路径；前端通过 `typecheck`、`build` 和浏览器人工验证确认 Cookie 自动携带与刷新体验。
- Rationale: AGENTS 要求高风险改动不能只凭代码改动完成判断。认证能力同时涉及接口、数据库、Cookie、外部邮件发送和真实页面行为，必须组合自动化与人工验证。
- Alternatives considered:
  - 仅单元测试：不足以覆盖 Cookie、数据库和刷新链路。
  - 仅手工点页面：难以稳定复现边界条件与限流路径。

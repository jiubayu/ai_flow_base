# 数据模型：邮箱验证码与密码认证

## 1. UserAccount

- 用途：表示系统中的可登录用户主体。
- 字段：
  - `user_id`: UUID，主键
  - `email`: 小写归一化邮箱地址，唯一
  - `email_verified_at`: 邮箱完成验证的时间，未验证时为空
  - `password_hash`: `scrypt` 密码摘要
  - `password_hash_version`: 摘要算法版本标识
  - `password_updated_at`: 最近一次密码设置或变更时间
  - `created_at`
  - `updated_at`
  - `last_login_at`
- 约束：
  - `email` 全局唯一，比较时必须使用归一化后的值。
  - 未验证邮箱不得进入可登录状态。
  - 密码必须满足“至少 8 位且包含字母和数字”的规则后才允许写入。
- 状态转移：
  - `pending_verification`：账号未创建前的候选状态，仅由验证码挑战承载
  - `verified_active`：完成注册并可登录

## 2. EmailVerificationChallenge

- 用途：表示一次用于注册邮箱校验的验证码挑战。
- 字段：
  - `challenge_id`: UUID，主键
  - `email`: 归一化邮箱地址
  - `purpose`: 固定为 `register`
  - `code_digest`: 验证码摘要，不存储明文
  - `expires_at`: 失效时间
  - `sent_at`: 最近一次发送时间
  - `used_at`: 被成功消费的时间
  - `invalidated_at`: 被新验证码替换或主动作废的时间
  - `window_started_at`: 当前限流统计窗口起始时间
  - `window_send_count`: 当前窗口已发送次数
  - `verify_attempt_count`: 已尝试校验次数
  - `last_attempt_at`
  - `created_at`
- 约束：
  - 同一 `email + purpose` 任一时刻仅允许 1 条“当前可用”挑战。
  - 60 秒内不得重复发送。
  - 15 分钟滚动窗口内最多 5 次发送。
  - 新挑战生效后旧挑战必须标记 `invalidated_at`。
  - 验证码默认 10 分钟内有效，且最多允许 5 次校验尝试。
- 状态转移：
  - `active` → `used`
  - `active` → `expired`
  - `active` → `replaced`
  - `active` → `attempts_exhausted`

## 3. AuthSession

- 用途：表示当前浏览器可用于访问受保护接口的短期登录会话。
- 字段：
  - `session_id`: 高熵随机字符串，主键
  - `user_id`: 关联 `UserAccount`
  - `refresh_grant_id`: 关联当前刷新资格
  - `issued_at`
  - `expires_at`
  - `revoked_at`
  - `last_seen_at`
  - `client_scope`: 浏览器会话范围标识
- 约束：
  - `session_id` 必须足够随机，不可预测。
  - 被撤销或过期的会话不得继续访问受保护接口。
  - 登出仅撤销当前浏览器当前会话对应记录，不联动其他 `client_scope`。
- 状态转移：
  - `active` → `expired`
  - `active` → `revoked`
  - `active` → `replaced`（刷新后旧 access 会话失效）

## 4. RefreshGrant

- 用途：表示当前浏览器会话的长期续期资格。
- 字段：
  - `refresh_grant_id`: 高熵随机字符串，主键
  - `user_id`: 关联 `UserAccount`
  - `client_scope`: 浏览器会话范围标识
  - `rotated_from_id`: 上一份刷新资格 ID，可为空
  - `issued_at`
  - `expires_at`
  - `revoked_at`
  - `replaced_by_id`: 新资格 ID，可为空
  - `last_used_at`
- 约束：
  - 每次刷新成功后，旧 `refresh_grant_id` 必须立刻写入 `revoked_at` 与 `replaced_by_id`。
  - 已撤销、已替换或已过期的资格不得再次刷新。
  - 当前浏览器登出时，当前 `client_scope` 下的现行刷新资格必须被撤销。
- 状态转移：
  - `active` → `rotated`
  - `active` → `expired`
  - `active` → `revoked`

## 5. AuthAuditEvent

- 用途：记录认证链路中的关键可审计事件，用于排查异常登录、验证码滥发与会话问题。
- 字段：
  - `event_id`: UUID，主键
  - `event_type`: `code_sent | code_rate_limited | register_succeeded | register_failed | login_succeeded | login_failed | refresh_succeeded | refresh_failed | logout_succeeded | logout_failed`
  - `user_id`: 可为空
  - `email`: 可为空，统一使用归一化邮箱
  - `client_scope`: 可为空
  - `occurred_at`
  - `outcome_code`: 机器可读结果码
  - `message`: 中文可读说明
- 约束：
  - 不得记录验证码明文、密码明文、Cookie 原值或 SMTP 密码等敏感信息。
  - 关键失败路径必须生成审计事件，不能静默吞没。

## 关系概览

- `UserAccount` 与 `AuthSession`：一对多
- `UserAccount` 与 `RefreshGrant`：一对多
- `UserAccount` 与 `AuthAuditEvent`：一对多（可为空）
- `EmailVerificationChallenge` 通过 `email` 与待注册用户建立前置关系
- `AuthSession` 必须绑定 1 个当前有效 `RefreshGrant`
- `RefreshGrant` 通过 `rotated_from_id`/`replaced_by_id` 形成单链轮换关系

## 迁移与兼容策略

- 升级路径：
  - 在现有 SQLite 数据库文件中新增 `user_accounts`、`email_verification_challenges`、`auth_sessions`、`refresh_grants`、`auth_audit_events` 表及必要索引。
  - 迁移脚本必须幂等，允许重复执行检查已存在对象。
- 回滚路径：
  - 若迁移失败，脚本停止执行并保留原数据库文件。
  - 若需回滚，按表级回滚脚本或备份文件恢复；不得在运行时自动删除已有表。
- 兼容发布策略：
  - 首次交付允许认证模块与现有 demo task 表并存于同一数据库文件。
  - 新增非空字段必须在建表时一次性提供默认约束，不依赖线上存量数据回填。
- 验证方式：
  - 迁移脚本执行后检查表、唯一索引和关键列是否存在。
  - 通过认证契约测试和集成测试验证注册、登录、刷新、登出链路。

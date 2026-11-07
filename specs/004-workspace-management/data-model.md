# Data Model: 工作空间与成员管理

## Entity: Workspace

**Purpose**: 表示独立数据边界和协作范围。

**Fields**:

- `workspace_id`: 全局唯一标识。
- `name`: 工作空间显示名称，默认由系统根据用户名生成。
- `created_by_user_id`: 创建该工作空间的用户；存量迁移创建时为对应存量用户。
- `created_at`: 创建时间。
- `updated_at`: 更新时间。
- `status`: 工作空间状态；本期仅需要 `active`，保留状态字段用于未来归档/删除扩展。

**Relationships**:

- 一个 Workspace 有多个 WorkspaceMembership。
- 一个 Workspace 可被多个 WorkspaceAuditEvent 引用。
- 工作空间内业务数据必须引用 `workspace_id`。

**Validation Rules**:

- `workspace_id` 必须唯一且不可变。
- `name` 必须非空。
- 本期不得删除或归档工作空间。

## Entity: WorkspaceMembership

**Purpose**: 表示用户与工作空间之间的归属关系和角色。

**Fields**:

- `membership_id`: 全局唯一标识。
- `workspace_id`: 所属工作空间。
- `user_id`: 成员用户。
- `role`: `manager` 或 `member`。
- `status`: `active` 或 `removed`。
- `joined_at`: 加入时间。
- `removed_at`: 移出时间，可为空。
- `created_by_user_id`: 添加该成员的操作者，可为空用于迁移。
- `updated_at`: 更新时间。

**Relationships**:

- 多个 WorkspaceMembership 属于一个 Workspace。
- 一个 UserAccount 可拥有多个 WorkspaceMembership。

**Validation Rules**:

- 同一 `(workspace_id, user_id)` 不得存在重复 active 成员关系。
- `role` 只能是 `manager` 或 `member`。
- 普通成员不能添加成员、删除成员或变更角色。
- 管理者可以添加成员、删除成员、变更角色。
- 删除成员或角色降级不得让工作空间失去最后一个 active manager。
- 被移出的成员必须立即失去该工作空间访问权限。

**State Transitions**:

```text
active(manager) ──role change──> active(member)
active(member)  ──role change──> active(manager)
active(*)       ──remove───────> removed(*)
```

限制：最后一个 active manager 不能转为 member，也不能被移除。

## Entity: UserWorkspacePreference

**Purpose**: 记录用户上次选择的工作空间，用于登录和会话查询时确定当前工作空间。

**Fields**:

- `user_id`: 用户标识，唯一。
- `last_workspace_id`: 用户上次选择的工作空间。
- `updated_at`: 更新时间。

**Validation Rules**:

- `last_workspace_id` 必须指向用户仍拥有 active 成员关系的工作空间；若不再可访问，系统必须选择任一仍可访问工作空间并更新偏好。
- 用户没有可访问工作空间时，会话应返回无可用工作空间状态，而不是暴露其他工作空间。

## Entity: WorkspaceAuditEvent

**Purpose**: 记录工作空间成员管理和角色变更相关事件，支持审计和问题定位。

**Fields**:

- `event_id`: 全局唯一标识。
- `event_type`: 事件类型，例如 `workspace_created`、`member_added`、`member_removed`、`member_role_changed`、`workspace_switched`。
- `workspace_id`: 目标工作空间。
- `actor_user_id`: 操作者，可为空用于系统迁移。
- `target_user_id`: 目标用户，可为空。
- `outcome_code`: 结果码，例如 `MEMBER_ADDED`、`MEMBER_ALREADY_EXISTS`、`LAST_MANAGER_PROTECTED`。
- `message`: 可读说明，不包含密码、Token、密钥或完整连接串。
- `occurred_at`: 发生时间。

**Validation Rules**:

- 成员添加、删除、角色变更、拒绝越权和最后管理者保护必须记录审计事件。
- 事件必须包含足够定位上下文：操作者、目标用户、工作空间、结果、时间。

## Entity: WorkspaceScopedBusinessData

**Purpose**: 表示所有需要工作空间隔离的业务数据集合。

**Fields**:

- `workspace_id`: 所属工作空间。
- 原业务字段保持不变。

**Validation Rules**:

- 所有读取、创建、修改、删除必须带有明确当前工作空间上下文。
- 创建时必须写入当前工作空间 `workspace_id`。
- 读取、修改、删除必须验证请求用户属于该工作空间。
- 存量数据迁移后不得存在无 `workspace_id` 的业务数据。

**Known Current Scope**:

- 当前已确认的认证表：`user_accounts`、`auth_sessions`、`refresh_grants`、`auth_audit_events` 不属于工作空间内业务数据，但会话响应需要关联工作空间上下文。
- 其他业务表需在实施阶段从数据库 schema 和代码引用中列出，逐表加入 `workspace_id` 或等价隔离字段。

## Migration Plan

**Upgrade Path**:

1. 新增 `workspaces`、`workspace_memberships`、`user_workspace_preferences`、`workspace_audit_events` 表和必要索引。
2. 为每个没有默认工作空间的存量用户创建一个 active 工作空间。
3. 为每个存量用户创建其默认工作空间中的 active manager 成员关系。
4. 为每个存量用户设置 `user_workspace_preferences.last_workspace_id`。
5. 对所有已识别的工作空间内业务数据表增加兼容 `workspace_id` 字段，先允许为空。
6. 按用户归属将存量业务数据回填到对应默认工作空间。
7. 增加验证 SQL，确认每个用户至少一个工作空间、每个工作空间至少一个管理者、成员关系无重复、业务数据无缺失归属。
8. 确认应用代码全量按工作空间上下文读写后，再考虑收紧非空约束。

**Rollback Path**:

- 上线前备份 SQLite 数据库文件。
- 若迁移失败且未发布新代码，恢复备份文件。
- 若已发布新代码但验证失败，回滚应用版本并恢复备份；不得保留部分回填数据继续运行。

**Idempotency**:

- 表创建使用 `CREATE TABLE IF NOT EXISTS`。
- 存量默认工作空间创建前按用户检查是否已存在由迁移创建或已关联的默认工作空间。
- 成员关系插入使用唯一约束或存在性检查避免重复。
- 回填业务数据时只更新 `workspace_id IS NULL` 的记录。

**Validation SQL Examples**:

```sql
SELECT user_id FROM user_accounts
WHERE user_id NOT IN (
  SELECT user_id FROM workspace_memberships WHERE status = 'active'
);

SELECT workspace_id FROM workspaces
WHERE workspace_id NOT IN (
  SELECT workspace_id FROM workspace_memberships
  WHERE status = 'active' AND role = 'manager'
);

SELECT workspace_id, user_id, COUNT(*)
FROM workspace_memberships
WHERE status = 'active'
GROUP BY workspace_id, user_id
HAVING COUNT(*) > 1;
```

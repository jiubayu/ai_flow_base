# 数据模型：应用工作空间与编排画布

## 1. UserAccount（既有）

- 用途：表示已认证用户主体，本功能通过现有认证会话获取当前 `user_id`。
- 相关字段：
  - `user_id`: UUID，主键
  - `email`: 归一化邮箱地址
- 约束：
  - 所有工作空间接口必须从当前有效会话解析用户身份，不接受客户端传入的 `user_id` 作为权限依据。
  - 未登录或会话失效用户不得访问工作空间接口。

## 2. Workspace

- 用途：表示用户登录后默认进入的个人工作空间。
- 字段：
  - `workspace_id`: UUID，主键
  - `owner_user_id`: 关联 `UserAccount.user_id`
  - `name`: 工作空间名称，首版可自动生成，例如“我的工作空间”
  - `is_default`: 是否为该用户默认工作空间
  - `created_at`
  - `updated_at`
- 约束：
  - 每个用户至少拥有 1 个默认个人工作空间。
  - 同一用户首版只允许 1 个默认工作空间。
  - 用户首次登录且无默认工作空间时，系统自动创建默认工作空间。
  - 用户只能读取和操作自己拥有的工作空间。
- 状态转移：
  - `missing` → `active`：首次访问工作空间时自动创建。
  - 首版不提供归档、删除或转移所有者。

## 3. WorkspaceApplication

- 用途：表示工作空间中以卡片展示并可进入详情的应用。
- 字段：
  - `application_id`: UUID，主键
  - `workspace_id`: 关联 `Workspace.workspace_id`
  - `owner_user_id`: 冗余记录所属用户，用于查询隔离和审计
  - `name`: 应用名称
  - `description`: 应用说明，可为空字符串
  - `status`: 应用状态，首版由系统维护，建议初始为 `draft`
  - `created_at`
  - `updated_at`
- 约束：
  - 同一 `workspace_id` 内 `name` 必须唯一。
  - `name` 必须去除首尾空白后非空，长度建议限制为 1-80 个字符。
  - `description` 可为空，长度建议限制为 0-500 个字符。
  - 创建和编辑名称时都必须检查同一工作空间内重名。
  - 首版允许编辑 `name` 和 `description`，不允许删除应用，不允许用户直接编辑 `status`。
  - 用户只能读取和修改自己工作空间下的应用。
- 状态转移：
  - `draft`：应用创建后的首版默认状态。
  - 首版不提供发布、归档、删除、运行或调试状态转移。

## 4. ApplicationCard（读取模型）

- 用途：工作空间页面中展示单个应用摘要和进入入口。
- 字段：
  - `application_id`
  - `name`
  - `description`
  - `status`
  - `updated_at`
- 约束：
  - 卡片数据只能来源于当前用户自己的工作空间。
  - 卡片必须能引导用户进入应用详情。

## 5. ApplicationCanvasView（读取模型）

- 用途：应用详情右侧的首版编排画布视图。
- 字段：
  - `application_id`
  - `mode`: 固定为 `empty`
  - `editable`: 固定为 `false`
  - `entry_label`: 开始编排入口文案
- 约束：
  - 首版始终展示空画布和入口。
  - 首版不得返回可编辑节点、边、流程定义或运行配置。

## 关系概览

- `UserAccount` 与 `Workspace`：一对多，首版每个用户只有 1 个默认个人工作空间。
- `Workspace` 与 `WorkspaceApplication`：一对多。
- `WorkspaceApplication` 与 `ApplicationCard`：一对一读取投影。
- `WorkspaceApplication` 与 `ApplicationCanvasView`：一对一读取投影，首版为空画布。

## 迁移与兼容策略

- 升级路径：
  - 在现有 SQLite 数据库文件中新增 `workspaces` 与 `workspace_applications` 表。
  - 为 `workspaces(owner_user_id, is_default)` 增加默认工作空间唯一约束或等价唯一索引。
  - 为 `workspace_applications(workspace_id, name)` 增加唯一约束或等价唯一索引。
  - 提供 `server/scripts/migrate_workspace_schema.py` 作为显式迁移入口。
- 回滚路径：
  - 迁移执行前建议备份本地 SQLite 文件。
  - 若迁移失败，脚本停止并保留原数据库文件。
  - 若需回滚首版新增 schema，可在确认无业务数据保留要求后删除 `workspace_applications` 与 `workspaces` 表，或恢复迁移前数据库备份。
- 兼容发布策略：
  - 新表与现有认证表并存，不修改认证表结构。
  - 默认工作空间按用户首次访问懒创建，不需要对所有既有用户执行一次性全量回填。
  - 新增非空字段在创建新表时提供明确写入值，不依赖后续无界回填。
- 验证方式：
  - 迁移脚本重复执行不报错。
  - 验证 `workspaces`、`workspace_applications` 表和唯一索引存在。
  - 使用两个用户创建同名应用，确认不同工作空间允许重名；同一工作空间创建或编辑为重名会失败。
  - 查询数据库确认首次访问后仅为当前用户创建 1 个默认工作空间。

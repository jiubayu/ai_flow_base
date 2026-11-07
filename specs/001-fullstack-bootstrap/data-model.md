# 数据模型：前后端工程初始化与启停脚本

## 1. ServiceDefinition

- 用途：描述一个可由统一脚本管理的本地服务。
- 字段：
  - `name`: `frontend | backend | celery`
  - `workdir`: 服务工作目录
  - `start_command`: 启动命令
  - `health_probe`: 用于判断服务可用的探针定义
  - `log_path`: 日志文件路径
  - `pid_path`: 进程 PID 文件路径
  - `dependencies`: 启动前依赖的配置或其他服务
- 约束：
  - `name` 全局唯一。
  - 所有服务都必须声明 `log_path` 与 `pid_path`。
  - `celery` 依赖 `backend` 的共享配置，但仍是独立进程。

## 2. ConfigTemplate

- 用途：表达前后端本地配置模板及其必填项。
- 字段：
  - `scope`: `server | ui`
  - `template_path`: 模板文件路径
  - `required_keys`: 必填配置项列表
  - `optional_keys`: 可选配置项列表
  - `placeholder_only`: 是否仅允许占位示例值
- 约束：
  - `required_keys` 不能为空。
  - 模板中不得包含真实凭据。
  - 若缺少必填配置，脚本与服务必须显式失败。

## 3. StartupSession

- 用途：描述一次通过统一脚本发起的启动流程。
- 字段：
  - `session_id`: 启动会话标识
  - `started_at`: 启动时间
  - `requested_services`: 目标服务列表
  - `results`: 每个服务的启动结果
  - `validation_state`: 联通验证状态
- 状态流转：
  - `pending` -> `starting` -> `running`
  - `pending` -> `starting` -> `failed`
  - `running` -> `stopping` -> `stopped`
- 约束：
  - 启动结果必须记录到日志或状态输出。
  - 任一服务失败时，会话状态不可标记为 `running`。

## 4. ServiceRuntimeStatus

- 用途：描述单个服务在本地开发环境中的当前运行状态。
- 字段：
  - `service_name`
  - `state`: `stopped | starting | running | failed | unknown`
  - `pid`
  - `last_check_at`
  - `status_message`
- 约束：
  - `state=running` 时必须能关联到有效 PID 或有效健康探针结果。
  - `status_message` 必须对失败原因可读。

## 5. DemoTask

- 用途：表达用于最小联通验证的异步示例任务。
- 字段：
  - `task_id`
  - `message`
  - `submitted_at`
  - `started_at`
  - `finished_at`
  - `state`: `PENDING | STARTED | SUCCESS | FAILURE`
  - `result_message`
  - `error_message`
- 状态流转：
  - `PENDING` -> `STARTED` -> `SUCCESS`
  - `PENDING` -> `STARTED` -> `FAILURE`
- 约束：
  - `task_id` 全局唯一。
  - `SUCCESS` 与 `FAILURE` 互斥。
  - `FAILURE` 时必须记录 `error_message`。

## 6. ConnectivityProbe

- 用途：表达一次最小联通验证步骤。
- 字段：
  - `probe_name`
  - `source`: `frontend | backend | script`
  - `target`: `backend | celery`
  - `method`: `http | task_dispatch | task_poll`
  - `expected_outcome`
  - `timeout_seconds`
- 约束：
  - 至少存在两类探针：`frontend -> backend` 与 `backend -> celery`。
  - 所有探针失败都必须产生明确错误输出。

## 关系概览

- `StartupSession` 聚合多个 `ServiceRuntimeStatus`。
- `ServiceDefinition` 定义 `ServiceRuntimeStatus` 的期望行为和探针。
- `ConnectivityProbe` 使用 `DemoTask` 验证 `backend -> celery` 链路。
- `ConfigTemplate` 为 `ServiceDefinition` 提供启动前置条件。

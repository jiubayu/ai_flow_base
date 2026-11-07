# 研究记录：前后端工程初始化与启停脚本

## 决策 1：仓库结构采用 `server/ + ui/ + scripts/`

- Decision: 使用双工程结构承载前后端，并用 `scripts/devctl.sh` 作为统一入口。
- Rationale: 该结构直接匹配 [AGENTS.md](../../AGENTS.md) 中既有运行命令和技术栈约束，能最小化后续命令、日志和测试路径的偏差。
- Alternatives considered:
  - 单工程混合前后端：会削弱前端 feature-based 与后端 DDD 分层边界。
  - 再拆分独立 worker 工程：对当前仅需本地 bootstrap 的范围来说过重。

## 决策 2：后端保持 DDD + 整洁架构，但只实现 bootstrap 相关最小领域

- Decision: 在 `server/src` 下保留 `domain/application/infrastructure/presentation` 分层，仅围绕启动验证、示例任务和运行状态建模。
- Rationale: 这样既满足架构约束，也避免为尚不存在的业务能力提前建模。
- Alternatives considered:
  - 全部逻辑直接写在 FastAPI 路由中：违反后端业务逻辑不得直接依赖基础设施的约束。
  - 过度抽象出通用平台层：会放大当前 feature 的实现体量。

## 决策 3：本地 Celery 链路使用文件系统 broker + SQLite 结果存储

- Decision: 使用文件系统目录承载 Celery broker 队列，并使用 SQLite 保存任务结果状态。
- Rationale: 该方案不需要新增 Redis、RabbitMQ 等外部基础设施，仍能支持“后端提交任务、worker 实际处理、接口轮询状态”的最小可验证链路。
- Alternatives considered:
  - Redis broker/result backend：实现更常见，但属于新增外部基础设施，当前未获批准。
  - `memory://`：无法支撑独立进程间的真实 worker 验证。
  - 仅记录日志不暴露任务状态：不足以支撑清晰的联通验收。

## 决策 4：统一脚本只负责 `start` / `stop` / `status`

- Decision: `scripts/devctl.sh` 仅提供 `start`、`stop`、`status` 三个公开子命令。
- Rationale: 这与澄清结果一致，避免把依赖安装、环境初始化等行为塞进脚本导致边界不清。
- Alternatives considered:
  - 增加 `init`、`verify` 等命令：可行，但会扩大当前范围。
  - 拆成多个脚本：入口分散，不利于新开发者使用。

## 决策 5：最小联通验证以“前端调用后端 + 后端提交示例任务并轮询成功”为准

- Decision: 前端加载时调用后端健康接口；后端提供提交示例任务与查询任务状态的开发接口；worker 实际执行任务并返回可见结果。
- Rationale: 这条链路能同时验证 HTTP、Celery 路由、结果存储与日志输出，比“单点健康检查”更能证明骨架可用。
- Alternatives considered:
  - 只验证后端健康接口：无法覆盖 worker。
  - 直接做完整业务流：超出 bootstrap 范围。

## 决策 6：日志与状态文件集中落在后端工作区

- Decision: 后端与 Celery 日志写入 `server/logs/`，脚本 PID/状态文件写入 `server/.runtime/`，前端 dev server 输出也由统一脚本汇总到 `server/logs/frontend.log`。
- Rationale: 这满足 AGENTS 的日志定位约束，并让排障入口集中。
- Alternatives considered:
  - 分散日志到各工程默认目录：会增加排障成本。
  - 仅依赖控制台输出：不满足“可定位日志文件”的要求。

## 决策 7：配置模板只提供示例值与必填说明，不注入真实敏感值

- Decision: 为前后端分别提供 `.env.example`，通过文档说明哪些字段必须由开发者自行填写。
- Rationale: 满足初始化体验要求，同时符合不得输出敏感信息和不得假定真实配置已可用的约束。
- Alternatives considered:
  - 自动生成完整 `.env`：容易形成误导性默认值。
  - 完全不提供模板：会降低首次启动成功率。

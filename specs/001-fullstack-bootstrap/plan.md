# Implementation Plan: 前后端工程初始化与启停脚本

**Branch**: `001-fullstack-bootstrap` | **Date**: 2026-05-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-fullstack-bootstrap/spec.md`

## Summary

初始化一个本地可运行的全栈开发骨架：`ui` 提供 React + Tailwind CSS + shadcn/ui 的前端入口，`server` 提供 FastAPI + Celery 的后端与异步任务入口，`scripts/devctl.sh` 作为统一入口管理 `start`、`stop`、`status`。为避免新增未批准的外部基础设施，本地异步链路采用文件系统 broker + SQLite 结果存储完成最小示例任务验证，并通过日志文件与健康接口支撑验收。

## Technical Context

**Language/Version**: Python 3.11，TypeScript 5.x，Bash

**Primary Dependencies**: FastAPI，SQLAlchemy，LangChain，Celery，React，Tailwind CSS，shadcn/ui，uv，pnpm

**Storage**: SQLite（本地结果状态与后续后端持久化入口），文件系统目录（日志、PID、Celery broker 队列）

**Testing**: pytest（单元/集成），后端接口 smoke 验证，Celery 最小任务集成验证，前端手工运行验证，统一脚本状态验证

**Target Platform**: Linux/macOS 本地开发环境，支持 Python 与 Node.js 工具链

**Project Type**: 全栈 Web 应用 + 异步 worker + 开发者 CLI 脚本

**Performance Goals**: 已完成依赖安装后，统一脚本可在 3 分钟内拉起三类服务；后端健康接口在本地开发机上 1 秒内返回；最小 Celery 示例任务在 10 秒内进入终态

**Constraints**: 必须遵守前端 feature-based 结构与后端 DDD + 整洁架构；日志输出到 `server/logs/`；不得使用静默兜底；不得依赖未批准的额外基础设施服务；配置模板不得包含真实敏感值

**Scale/Scope**: 单仓库、3 个可运行进程、1 个前端状态页、1 组后端健康与示例任务接口、1 个统一脚本入口，仅覆盖本地开发场景

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`：虽然 [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) 仍是占位模板，当前实现约束以 [AGENTS.md](../../AGENTS.md) 为实际治理文件。
- `PASS`：前端方案限定为 React + Tailwind CSS + shadcn/ui，并采用 feature-based 目录，不引入额外 UI 框架。
- `PASS`：后端方案限定为 FastAPI + SQLAlchemy + LangChain + Celery，并采用 `domain/application/infrastructure/presentation` 分层，不让业务逻辑直接依赖基础设施实现。
- `PASS`：本地异步链路采用文件系统 broker + SQLite 结果存储，避免新增 Redis 等外部基础设施，符合“未经批准不得新增外部平台”。
- `PASS`：验收路径覆盖自动化与可观察性，包含 pytest、接口 smoke、Celery 最小任务验证、脚本状态验证和日志检查。
- `PASS`：当前设计不涉及已有数据库 schema 变更，因此无数据迁移阻断项；若后续引入真实业务表结构，需另补迁移方案。

### Post-Design Constitution Check

- `PASS`：设计产物已将日志文件、最小联通验证、错误显式化和脚本边界写入 contract 与 quickstart。
- `PASS`：设计未扩展到生产部署、远程环境编排或复杂业务链路，保持最小实现范围。

## Project Structure

### Documentation (this feature)

```text
specs/001-fullstack-bootstrap/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── backend-dev-api.openapi.yaml
│   └── devctl-cli.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
└── devctl.sh

server/
├── pyproject.toml
├── .env.example
├── src/
│   ├── main.py
│   ├── celery_app.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── domain/
│   │   └── bootstrap/
│   │       ├── entities.py
│   │       └── value_objects.py
│   ├── application/
│   │   └── bootstrap/
│   │       ├── services.py
│   │       └── use_cases.py
│   ├── infrastructure/
│   │   ├── celery/
│   │   │   ├── broker.py
│   │   │   └── tasks.py
│   │   ├── persistence/
│   │   │   └── result_store.py
│   │   └── logging/
│   │       └── file_logger.py
│   └── presentation/
│       └── api/
│           ├── health.py
│           └── dev_tasks.py
├── tests/
│   ├── unit/
│   └── integration/
└── logs/

ui/
├── package.json
├── .env.example
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   └── providers/
│   ├── features/
│   │   └── bootstrap-status/
│   │       ├── api.ts
│   │       ├── components/
│   │       └── hooks/
│   ├── shared/
│   │   ├── components/
│   │   ├── lib/
│   │   └── styles/
│   └── main.tsx
└── public/
```

**Structure Decision**: 采用双工程结构 `server/ + ui/ + scripts/`。后端在 `server/src` 内用 DDD + 整洁架构分层，前端在 `ui/src` 内按 feature 组织页面状态，统一启停能力收敛到 `scripts/devctl.sh`，避免把运维式逻辑散落到前后端工程内部。

## Complexity Tracking

无宪章违规项，无需复杂度豁免。

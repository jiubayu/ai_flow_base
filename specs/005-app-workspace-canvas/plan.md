# Implementation Plan: 应用工作空间与编排画布

**Branch**: `005-app-workspace-canvas` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-app-workspace-canvas/spec.md`

## Summary

新增登录后默认进入个人工作空间的全栈垂直切片：后端在认证会话之上提供工作空间自动初始化、应用创建、卡片列表、应用详情、应用名称/说明编辑与权限隔离；前端新增 `workspace` feature，在登录后展示工作空间应用卡片，并进入应用详情的左右分栏布局。首版编排画布只展示空画布和开始编排入口，不提供节点编辑、流程保存、运行或调试能力。实现沿用现有 FastAPI + DDD/整洁架构、SQLite 迁移脚本、React + Tailwind + shadcn/ui 风格；前端页面路由按用户批准引入 `react-router-dom`（路径式 URL，每个页面一条路由），除此之外不新增第三方依赖。

## Technical Context

**Language/Version**: Python 3.11，TypeScript 5.x，React 18，Vite 5

**Primary Dependencies**: FastAPI，Pydantic，SQLAlchemy 2.x，React，Tailwind CSS，shadcn/ui 风格组件，浏览器 Fetch API，`react-router-dom`（用户批准的前端路由依赖）；复用现有 HTTP Only Cookie 认证能力与共享 HTTP 工具

**Storage**: SQLite（复用 `server/.runtime` 下现有数据库文件并新增 workspace/application 表），HTTP Only Cookie，文件日志

**Testing**: `pytest` 单元/契约/集成测试，`pnpm run typecheck`，`pnpm run build`，前端页面运行与浏览器日志验证，后端日志和 SQLite 数据验证

**Target Platform**: 本地开发环境下的 Linux/macOS 后端进程与现代桌面浏览器

**Project Type**: 全栈 Web 应用工作空间与应用管理切片（FastAPI API + React feature）

**Performance Goals**: 95% 的已登录用户在 2 秒内看到工作空间首屏；用户可在 1 分钟内创建首个应用并看到卡片；用户可在 2 次点击以内从工作空间进入应用详情；应用名称/说明编辑在 1 分钟内完成并在列表与详情中保持一致

**Constraints**: 必须遵守后端 DDD + 整洁架构、前端 feature-based 结构和既有主题/组件体系；不得新增未批准第三方依赖（`react-router-dom` 已由用户批准，仅用于前端页面路由）；所有受保护工作空间接口必须通过当前认证会话确定用户；禁止跨用户读取或修改工作空间与应用；同一工作空间内应用名称唯一；首版不得提供删除应用或流程节点编辑能力；涉及 schema 变更必须提供幂等迁移脚本、验证方式和失败恢复说明；后端 debug 日志需完整体现工作空间和应用数据流转且不得输出 Cookie 原值或敏感信息

**Scale/Scope**: 单仓库内新增 1 套 workspace 域模型、1 组后端工作空间 API、1 个前端 `workspace` feature、1 份 API/UI 契约、1 份数据升级方案与验证说明；范围仅覆盖个人默认工作空间、应用创建/列表/详情/名称说明编辑、空编排画布入口，不包含组织空间、多成员协作、应用删除、节点编辑、流程保存、运行调试或发布

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`：虽然 [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) 仍是占位模板，当前治理以 [AGENTS.md](../../AGENTS.md) 为实际约束来源。
- `PASS`：后端方案限定为 FastAPI + SQLite 持久化 + `domain/application/infrastructure/presentation` 分层，业务逻辑通过领域对象和应用用例表达，不让应用层直接依赖基础设施实现。
- `PASS`：前端方案限定为 React + Tailwind CSS + shadcn/ui 风格组件，新增 `ui/src/features/workspace` 并复用共享 HTTP、主题 token 与基础 UI 组件，不绕过现有组件体系。
- `PASS`：未引入未批准第三方依赖；`react-router-dom` 是用户明确批准的路由依赖（2026-11-07 决定：引入 react-router-dom + 路径式 URL），除此之外未新增；画布首版采用静态空画布和入口，不引入画布/流程编排第三方库。
- `PASS`：数据库变更纳入设计范围，将通过显式迁移脚本、回滚说明、验证 SQL/测试和真实接口校验满足 AGENTS 的数据升级要求。
- `PASS`：验收路径覆盖自动化与真实链路验证，包含 pytest、前端类型检查/构建、浏览器页面验证、后端日志检查和 SQLite 数据状态验证。

### Post-Design Constitution Check

- `PASS`：设计产物将后端改动限制在 `server/src/domain/workspace`、`server/src/application/workspace`、`server/src/infrastructure/persistence/*workspace*`、`server/src/presentation/api/workspace.py`、`server/src/main.py` 和迁移脚本等必要路径中。
- `PASS`：设计产物将前端改动限制在 `ui/src/features/workspace`、`ui/src/features/auth`（页面与 `providers/AuthProvider`）、`ui/src/app/`（`App.tsx`、`router.tsx`、`guards/`、`components/`）和共享 HTTP 类型安全调用边界内，符合 feature-based 结构；路由装配只在 `ui/src/app/`，feature 不反向依赖 app。
- `PASS`：契约和数据模型明确了工作空间自动创建、用户隔离、应用名称唯一、编辑字段范围、禁止删除、空画布不可编辑等核心约束。
- `PASS`：quickstart 包含迁移、启动、真实接口、浏览器页面、日志和数据库验证步骤，不以代码改动本身作为完成依据。

## Project Structure

### Documentation (this feature)

```text
specs/005-app-workspace-canvas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── workspace-api.openapi.yaml
│   └── workspace-ui-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
server/
├── scripts/
│   └── migrate_workspace_schema.py
├── src/
│   ├── main.py
│   ├── domain/
│   │   └── workspace/
│   │       ├── entities.py
│   │       └── value_objects.py
│   ├── application/
│   │   └── workspace/
│   │       ├── ports.py
│   │       └── use_cases.py
│   ├── infrastructure/
│   │   └── persistence/
│   │       ├── workspace_migrations.py
│   │       └── workspace_repository.py
│   └── presentation/
│       └── api/
│           └── workspace.py
└── tests/
    ├── contract/
    │   └── test_workspace_api.py
    ├── integration/
    │   └── test_workspace_flow.py
    └── unit/
        └── workspace/

ui/
└── src/
    ├── app/
    │   └── App.tsx
    ├── features/
    │   ├── auth/
    │   └── workspace/
    │       ├── api.ts
    │       ├── components/
    │       ├── hooks/
    │       └── pages/
    └── shared/
        ├── components/
        └── lib/
            └── http.ts
```

**Structure Decision**: 采用现有双工程仓库结构。后端新增 `workspace` 垂直切片，领域层表达工作空间、应用与名称唯一规则，应用层编排当前用户的默认工作空间初始化、应用创建、列表、详情和编辑，用基础设施层 SQLite repository 与迁移脚本落地，表现层暴露 `/api/workspace` 相关接口。前端新增 `ui/src/features/workspace`，以工作空间页面、应用卡片、应用详情布局、应用表单和空画布组件组织 UI，登录后的主应用入口从认证状态进入工作空间。

## Complexity Tracking

无宪章违规项，无需复杂度豁免。

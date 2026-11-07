# Implementation Plan: 工作空间与成员管理

**Branch**: `004-workspace-management` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-workspace-management/spec.md`

## Summary

实现工作空间作为用户数据隔离和协作边界：注册成功后自动创建默认工作空间并赋予注册用户管理者角色；存量用户启用工作空间时创建默认工作空间并迁移现有数据归属；用户会话返回当前工作空间、可访问工作空间和角色；管理者可通过用户名添加已注册用户、删除成员、变更成员角色；普通成员可操作当前工作空间内业务数据但不能管理成员。技术实现采用后端 DDD + 整洁架构新增 workspace 领域与应用用例，通过 SQLite 迁移提供工作空间、成员关系、用户工作空间偏好和审计事件表，前端按 feature-based 新增 workspace API 与工作空间上下文展示/切换能力。

## Technical Context

**Language/Version**: Python >=3.11；TypeScript 5.6；React 18.3

**Primary Dependencies**: FastAPI、Pydantic、SQLite 标准库、pytest/httpx；React、Tailwind CSS、现有 shadcn 风格 UI 组件；不新增第三方依赖

**Storage**: 当前本地 SQLite 数据库，路径由 `server/src/core/config.py` 的 `result_store_path` 提供；通过现有迁移入口扩展 schema

**Testing**: 后端 pytest 单元测试、集成测试、契约测试；前端 TypeScript typecheck；前端页面运行与浏览器日志验证

**Target Platform**: 本地 Linux 开发环境；后端 FastAPI 服务；前端 Vite 开发服务

**Project Type**: 全栈 Web 应用，后端 API + 前端 React UI

**Performance Goals**: 注册到进入默认工作空间流程 2 分钟内完成；成员添加/删除流程 1 分钟内完成；会话查询和工作空间切换在常规本地数据规模下用户可感知无明显等待

**Constraints**: 数据隔离必须基于明确工作空间上下文；越权访问拒绝率 100%；工作空间必须始终至少保留一个管理者；迁移必须可重复检查、可验证、避免无归属业务数据；不得新增依赖；不得绕过 DDD/整洁架构或前端 feature-based 结构

**Scale/Scope**: 本期覆盖认证用户、工作空间、成员关系、角色、当前工作空间偏好、成员管理 API、存量用户默认工作空间迁移；不覆盖邀请链接、工作空间删除/归档、所有权转让、计费、自定义角色、跨工作空间数据共享

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

项目宪章文件仍为模板占位，实际约束采用 `AGENTS.md`：

- **需求与验收**: PASS。规格已通过 checklist；计划包含后端测试、接口契约、迁移验证和前端运行验证。
- **代码修改边界**: PASS。仅规划 workspace 功能必要改动；不新增依赖；不要求回滚或覆盖现有未提交改动。
- **后端架构**: PASS。计划新增 domain/application/infrastructure/presentation 分层，业务规则放入领域和应用层，SQLite 实现留在基础设施层。
- **前端架构**: PASS。计划新增 `ui/src/features/workspace/` 并复用 shared HTTP 与现有 UI 组件。
- **数据升级**: PASS。计划包含兼容 schema 新增、存量用户默认工作空间回填、验证 SQL/测试和失败恢复说明。
- **日志与调试**: PASS。计划要求成员管理、工作空间切换、迁移关键路径输出 debug/info/error 日志，且不记录敏感信息。
- **测试要求**: PASS。后端覆盖单元、集成、契约测试；前端覆盖 typecheck 与页面运行验证。

## Project Structure

### Documentation (this feature)

```text
specs/004-workspace-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── workspace-api.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
server/
├── src/
│   ├── domain/
│   │   └── workspace/
│   │       ├── entities.py
│   │       ├── services.py
│   │       └── value_objects.py
│   ├── application/
│   │   └── workspace/
│   │       ├── ports.py
│   │       └── use_cases.py
│   ├── infrastructure/
│   │   └── persistence/
│   │       ├── workspace_migrations.py
│   │       └── workspace_repository.py
│   ├── presentation/
│   │   └── api/
│   │       └── workspace.py
│   └── main.py
└── tests/
    ├── contract/
    │   ├── test_auth_api.py
    │   └── test_workspace_api.py
    ├── integration/
    │   ├── test_auth_flow.py
    │   └── test_workspace_flow.py
    └── unit/
        └── workspace/
            └── test_workspace_rules.py

ui/
└── src/
    ├── features/
    │   ├── auth/
    │   │   ├── api.ts
    │   │   └── components/
    │   └── workspace/
    │       ├── api.ts
    │       ├── hooks/
    │       │   └── useWorkspaceSession.ts
    │       └── components/
    │           ├── WorkspaceSwitcher.tsx
    │           └── WorkspaceMembersPanel.tsx
    └── shared/
        ├── components/
        └── lib/
```

**Structure Decision**: 采用现有全栈结构。后端新增 `workspace` 领域、应用、基础设施和 API 路由；认证注册用例只编排 workspace 应用服务，不直接依赖数据库实现。前端新增 `features/workspace`，认证会话 API 扩展返回 workspace 上下文，工作空间切换和成员管理由独立 workspace feature 承载。

## Phase 0: Research

见 [research.md](./research.md)。所有技术未知项已通过本地代码调研和项目约束决策完成，无剩余 `NEEDS CLARIFICATION`。

## Phase 1: Design & Contracts

设计产物：

- [data-model.md](./data-model.md)
- [contracts/workspace-api.md](./contracts/workspace-api.md)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **架构分层**: PASS。领域对象、应用端口、SQLite 仓储、API 路由分离。
- **数据升级**: PASS。数据模型明确新增表、索引、回填、幂等检查和验证 SQL；不做破坏性删除。
- **测试与验收**: PASS。quickstart 覆盖迁移、契约、集成、单元和前端 typecheck。
- **日志与异常语义**: PASS。API contract 明确错误码；quickstart 要求检查 debug 日志。
- **范围控制**: PASS。明确排除邀请、工作空间删除、计费、自定义角色和所有权转让。

## Complexity Tracking

无宪章违规，无需复杂度豁免。

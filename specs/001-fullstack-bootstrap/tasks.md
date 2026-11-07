# Tasks: 前后端工程初始化与启停脚本

**Input**: Design documents from `/specs/001-fullstack-bootstrap/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 包含后端 contract、integration、unit 测试任务；前端以运行验证和日志验证为主，不新增组件级测试。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- 每个任务都包含明确文件路径，便于直接执行

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 初始化仓库骨架、依赖清单与基础目录

- [X] T001 Create bootstrap repository structure in scripts/devctl.sh, server/src/, server/tests/, ui/src/, server/logs/.gitkeep, and server/.runtime/.gitkeep
- [X] T002 Create backend dependency and environment manifests in server/pyproject.toml and server/.env.example
- [X] T003 [P] Create frontend dependency and environment manifests in ui/package.json, ui/tsconfig.json, ui/vite.config.ts, ui/tailwind.config.ts, and ui/.env.example
- [X] T004 [P] Configure generated file ignores in .gitignore and preserve runtime/log placeholders in server/logs/.gitkeep and server/.runtime/.gitkeep

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有用户故事都依赖的基础设施、分层骨架和运行入口

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement backend configuration and structured logging bootstrap in server/src/core/config.py, server/src/core/logging.py, and server/src/main.py
- [X] T006 [P] Implement Celery application wiring and filesystem broker configuration in server/src/celery_app.py and server/src/infrastructure/celery/broker.py
- [X] T007 [P] Implement bootstrap persistence foundation in server/src/infrastructure/persistence/result_store.py and server/src/domain/bootstrap/entities.py
- [X] T008 Implement backend API router registration and shared error handling in server/src/main.py, server/src/presentation/api/health.py, and server/src/presentation/api/dev_tasks.py
- [X] T009 [P] Create frontend app shell and shared style foundation in ui/src/main.tsx, ui/src/app/App.tsx, and ui/src/shared/styles/index.css
- [X] T010 [P] Create frontend shared HTTP client scaffold in ui/src/shared/lib/http.ts and ui/src/features/bootstrap-status/api.ts
- [X] T011 Implement devctl command skeleton and runtime path helpers in scripts/devctl.sh
- [X] T012 [P] Create backend test scaffolding and common fixtures in server/pytest.ini and server/tests/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 初始化并启动完整工程 (Priority: P1) 🎯 MVP

**Goal**: 让开发者完成依赖安装、配置模板准备、启动前端/后端/Celery，并通过最小联通验证确认工程骨架可用

**Independent Test**: 在全新环境中按 quickstart 完成依赖安装和配置后，手动启动前端、后端、Celery；访问 `/api/health` 成功，提交示例任务后可查询到 `SUCCESS`，前端页面能展示后端状态与任务结果

### Tests for User Story 1

- [X] T013 [P] [US1] Add API contract tests for bootstrap endpoints in server/tests/contract/test_bootstrap_api.py
- [X] T014 [P] [US1] Add integration test for backend-to-Celery demo task flow in server/tests/integration/test_demo_task_flow.py

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement bootstrap value objects and demo task entities in server/src/domain/bootstrap/value_objects.py and server/src/domain/bootstrap/entities.py
- [X] T016 [US1] Implement startup validation and demo task use cases in server/src/application/bootstrap/use_cases.py and server/src/application/bootstrap/services.py
- [X] T017 [US1] Implement Celery demo task execution and SQLite result mapping in server/src/infrastructure/celery/tasks.py and server/src/infrastructure/persistence/result_store.py
- [X] T018 [US1] Implement FastAPI health and demo task endpoints in server/src/presentation/api/health.py and server/src/presentation/api/dev_tasks.py
- [X] T019 [P] [US1] Implement frontend bootstrap status hook and API adapter in ui/src/features/bootstrap-status/hooks/useBootstrapStatus.ts and ui/src/features/bootstrap-status/api.ts
- [X] T020 [P] [US1] Build bootstrap status UI components in ui/src/features/bootstrap-status/components/BootstrapStatusPanel.tsx and ui/src/shared/components/StatusCard.tsx
- [X] T021 [US1] Integrate bootstrap status feature into ui/src/app/App.tsx and ui/src/main.tsx
- [X] T022 [US1] Update initialization and manual validation guidance in specs/001-fullstack-bootstrap/quickstart.md and README.md

**Checkpoint**: User Story 1 should now support manual startup and minimum connectivity verification without the unified script

---

## Phase 4: User Story 2 - 使用统一脚本管理启停 (Priority: P2)

**Goal**: 提供统一入口脚本管理前端、后端与 Celery 的启动、停止、状态查看和失败提示

**Independent Test**: 执行 `./scripts/devctl.sh start` 可启动 3 个服务并输出日志路径；执行 `status` 可显示 3 个服务状态；执行 `stop` 可清理所有服务；缺失配置、端口冲突和重复执行都会得到明确错误信息

### Tests for User Story 2

- [X] T023 [P] [US2] Add devctl lifecycle integration tests for start, stop, and status in server/tests/integration/test_devctl_cli.py
- [X] T024 [P] [US2] Add devctl failure-path tests for missing config, port conflict, and repeat execution in server/tests/integration/test_devctl_failures.py

### Implementation for User Story 2

- [X] T025 [US2] Implement devctl subcommand dispatch and service registry in scripts/devctl.sh
- [X] T026 [P] [US2] Implement runtime status read model and service definitions in server/src/domain/bootstrap/entities.py and server/src/application/bootstrap/services.py
- [X] T027 [US2] Implement process start/stop flow with PID persistence in scripts/devctl.sh and server/src/application/bootstrap/use_cases.py
- [X] T028 [US2] Implement explicit precondition checks, port validation, and stale PID cleanup in scripts/devctl.sh and server/src/core/config.py
- [X] T029 [US2] Implement script status output and log-linking behavior in scripts/devctl.sh and server/src/core/logging.py
- [X] T030 [US2] Align CLI contract and scripted workflow documentation in specs/001-fullstack-bootstrap/contracts/devctl-cli.md and specs/001-fullstack-bootstrap/quickstart.md

**Checkpoint**: User Story 2 should now provide a reliable single-entry local operations workflow

---

## Phase 5: User Story 3 - 理解工程结构与边界 (Priority: P3)

**Goal**: 让开发者快速理解目录职责、配置模板位置、日志位置和后续扩展边界

**Independent Test**: 仅阅读仓库说明文档即可定位前端入口、后端入口、Celery 入口、配置模板、日志目录和统一脚本，并知道后续新增代码应放在哪一层或哪个 feature 下

### Implementation for User Story 3

- [X] T031 [P] [US3] Add root onboarding and structure guide in README.md and scripts/README.md
- [X] T032 [P] [US3] Add backend layering and extension guidance in server/README.md and server/src/README.md
- [X] T033 [P] [US3] Add frontend feature-based structure guidance in ui/README.md and ui/src/features/bootstrap-status/README.md
- [X] T034 [US3] Annotate required configuration and log locations in server/.env.example and ui/.env.example
- [X] T035 [US3] Cross-link structure, boundary, and validation guidance in README.md and specs/001-fullstack-bootstrap/quickstart.md

**Checkpoint**: User Story 3 should now make the repository structure self-explanatory for the next developer

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 完成跨故事质量收尾、补强测试和最终验证

- [X] T036 [P] Add unit tests for config parsing and result-store edge cases in server/tests/unit/test_config.py and server/tests/unit/test_result_store.py
- [X] T037 [P] Harden sensitive-data-safe logging and failure messaging in server/src/core/logging.py and scripts/devctl.sh
- [X] T038 [P] Sync final API examples and quickstart commands in specs/001-fullstack-bootstrap/contracts/backend-dev-api.openapi.yaml and specs/001-fullstack-bootstrap/quickstart.md
- [X] T039 Run full quickstart validation and capture final documentation adjustments in README.md and specs/001-fullstack-bootstrap/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 可立即开始
- **Phase 2 (Foundational)**: 依赖 Phase 1 完成；阻塞全部用户故事
- **Phase 3 (US1)**: 依赖 Phase 2 完成；作为 MVP 优先交付
- **Phase 4 (US2)**: 依赖 Phase 2 完成，且最好在 US1 的服务链路可用后推进
- **Phase 5 (US3)**: 依赖 Phase 2 完成，可与 US2 部分并行，但最终文档应基于已落地实现收口
- **Phase 6 (Polish)**: 依赖所有目标用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: 无其他用户故事依赖，是 MVP
- **User Story 2 (P2)**: 依赖 US1 已提供可启动的前端、后端、Celery 链路
- **User Story 3 (P3)**: 依赖 US1/US2 基本结构和脚本能力已经明确，才能形成稳定文档

### Within Each User Story

- 后端 tests 先写并确保初始失败，再实现接口与服务
- 领域模型先于应用服务
- 应用服务先于接口或脚本整合
- 文档任务放在该故事功能基本落地后收口，避免与实现脱节

### Parallel Opportunities

- Phase 1 中的 T003、T004 可并行
- Phase 2 中的 T006、T007、T009、T010、T012 可并行
- US1 中的 T013 与 T014 可并行，T019 与 T020 可并行
- US2 中的 T023 与 T024 可并行，T026 可与 T025 局部并行
- US3 中的 T031、T032、T033 可并行
- Polish 中的 T036、T037、T038 可并行

---

## Parallel Example: User Story 1

```bash
# 并行准备 US1 的验证与前端能力
Task: "Add API contract tests for bootstrap endpoints in server/tests/contract/test_bootstrap_api.py"
Task: "Add integration test for backend-to-Celery demo task flow in server/tests/integration/test_demo_task_flow.py"
Task: "Implement frontend bootstrap status hook and API adapter in ui/src/features/bootstrap-status/hooks/useBootstrapStatus.ts and ui/src/features/bootstrap-status/api.ts"
Task: "Build bootstrap status UI components in ui/src/features/bootstrap-status/components/BootstrapStatusPanel.tsx and ui/src/shared/components/StatusCard.tsx"
```

---

## Parallel Example: User Story 2

```bash
# 并行准备脚本验证与状态模型
Task: "Add devctl lifecycle integration tests for start, stop, and status in server/tests/integration/test_devctl_cli.py"
Task: "Add devctl failure-path tests for missing config, port conflict, and repeat execution in server/tests/integration/test_devctl_failures.py"
Task: "Implement runtime status read model and service definitions in server/src/domain/bootstrap/entities.py and server/src/application/bootstrap/services.py"
```

---

## Parallel Example: User Story 3

```bash
# 并行补全文档边界
Task: "Add root onboarding and structure guide in README.md and scripts/README.md"
Task: "Add backend layering and extension guidance in server/README.md and server/src/README.md"
Task: "Add frontend feature-based structure guidance in ui/README.md and ui/src/features/bootstrap-status/README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. 依据 `server/tests/contract/test_bootstrap_api.py`、`server/tests/integration/test_demo_task_flow.py` 和 `specs/001-fullstack-bootstrap/quickstart.md` 验证 MVP
5. 确认前端、后端、Celery 的最小联通链路可运行后再继续

### Incremental Delivery

1. Setup + Foundational 完成后，先交付 US1 的手动启动与最小联通
2. 在 US1 稳定后交付 US2 的统一脚本体验
3. 在脚本能力稳定后交付 US3 的结构说明与扩展边界
4. 最后执行 Polish，统一补强测试、日志和文档

### Parallel Team Strategy

1. 一人完成 Phase 1 与 Phase 2 主干
2. 之后可拆分：
   - Developer A: US1 后端链路与契约测试
   - Developer B: US1 前端状态页与后续 US3 文档
   - Developer C: US2 `devctl` 脚本与失败路径验证
3. 合流后执行 Phase 6 的完整验证

---

## Notes

- 所有任务都遵循 `- [ ] Txxx ...` 清单格式
- `[P]` 仅用于不同文件、可以独立推进的任务
- `[US1]`、`[US2]`、`[US3]` 仅用于用户故事阶段任务
- 后端测试为必须项；前端以运行验证和日志验证为验收依据
- 实现过程中如需新增依赖，必须先获得用户批准

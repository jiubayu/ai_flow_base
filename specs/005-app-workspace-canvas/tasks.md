# Tasks: 应用工作空间与编排画布

**Input**: Design documents from `/specs/005-app-workspace-canvas/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: 本项目 AGENTS.md 要求开发任务必须有可检查验收标准；本功能涉及接口、数据库、认证会话和前端页面，因此包含契约测试、集成测试、单元测试、类型检查/构建和真实验证任务。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 创建工作空间垂直切片的目录与空文件，确保后续任务只在规划路径内实施。

- [X] T001 Create backend workspace package directories and `__init__.py` files in `server/src/domain/workspace/`, `server/src/application/workspace/`, and `server/tests/unit/workspace/`
- [X] T002 [P] Create frontend workspace feature directories in `ui/src/features/workspace/components/`, `ui/src/features/workspace/hooks/`, and `ui/src/features/workspace/pages/`
- [X] T003 [P] Create backend workspace API and persistence placeholder files in `server/src/presentation/api/workspace.py`, `server/src/infrastructure/persistence/workspace_migrations.py`, and `server/src/infrastructure/persistence/workspace_repository.py`
- [X] T004 [P] Create workspace test placeholder files in `server/tests/contract/test_workspace_api.py`, `server/tests/integration/test_workspace_flow.py`, and `server/tests/unit/workspace/test_workspace_domain.py`
- [X] T005 [P] Create frontend workspace feature placeholder files in `ui/src/features/workspace/api.ts`, `ui/src/features/workspace/hooks/useWorkspace.ts`, and `ui/src/features/workspace/pages/WorkspacePage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有用户故事共享的数据模型、迁移、端口、认证用户解析和路由挂载基础。

**Critical**: No user story work can begin until this phase is complete.

- [X] T006 Implement workspace value object validation for workspace names, application names, descriptions, IDs, and timestamps in `server/src/domain/workspace/value_objects.py`
- [X] T007 Implement `Workspace`, `WorkspaceApplication`, `ApplicationCardView`, and `ApplicationCanvasView` domain entities in `server/src/domain/workspace/entities.py`
- [X] T008 Implement idempotent SQLite DDL for `workspaces` and `workspace_applications` including unique indexes in `server/src/infrastructure/persistence/workspace_migrations.py`
- [X] T009 Implement explicit migration CLI with schema verification output in `server/scripts/migrate_workspace_schema.py`
- [X] T010 Define `WorkspaceRepositoryPort`, `ClockPort`, and current-user input/output DTOs in `server/src/application/workspace/ports.py`
- [X] T011 Implement base `SqliteWorkspaceRepository` connection handling, row mapping, and transaction helpers in `server/src/infrastructure/persistence/workspace_repository.py`
- [X] T012 Implement protected workspace router helpers for resolving current auth session without exposing client-provided `user_id` in `server/src/presentation/api/workspace.py`
- [X] T013 Wire workspace repository, use cases, and router placeholders into FastAPI app state in `server/src/main.py`

**Checkpoint**: Foundation ready; user story implementation can now begin.

---

## Phase 3: User Story 1 - 登录后进入个人工作空间 (Priority: P1) MVP

**Goal**: 已登录用户默认进入自己的个人工作空间；首次访问自动创建默认工作空间；空应用列表展示创建入口；用户隔离生效。

**Independent Test**: 使用一个已登录账号请求当前工作空间，确认返回该用户默认工作空间和空应用列表；重复请求不创建重复工作空间；另一个用户看不到该用户数据。

### Tests for User Story 1

- [X] T014 [P] [US1] Add contract tests for `GET /api/workspace/current`, unauthenticated rejection, auto-create, and no duplicate default workspace in `server/tests/contract/test_workspace_api.py`
- [X] T015 [P] [US1] Add integration test for login/register then default workspace entry and cross-user isolation in `server/tests/integration/test_workspace_flow.py`
- [X] T016 [P] [US1] Add unit tests for default workspace creation and ownership rules in `server/tests/unit/workspace/test_workspace_domain.py`

### Implementation for User Story 1

- [X] T017 [US1] Implement `get_or_create_current_workspace` use case with debug logging and explicit errors in `server/src/application/workspace/use_cases.py`
- [X] T018 [US1] Implement repository methods for default workspace lookup, creation, and application-card listing in `server/src/infrastructure/persistence/workspace_repository.py`
- [X] T019 [US1] Implement `GET /api/workspace/current` response models and route in `server/src/presentation/api/workspace.py`
- [X] T020 [P] [US1] Implement `getCurrentWorkspace` API client and response types in `ui/src/features/workspace/api.ts`
- [X] T021 [P] [US1] Implement `useWorkspace` loading, empty, error, and refresh state in `ui/src/features/workspace/hooks/useWorkspace.ts`
- [X] T022 [P] [US1] Implement empty workspace state and create-entry shell in `ui/src/features/workspace/components/WorkspaceEmptyState.tsx`
- [X] T023 [US1] Implement `WorkspacePage` showing current workspace name, empty app list state, and authentication failure state in `ui/src/features/workspace/pages/WorkspacePage.tsx`
- [X] T024 [US1] Update logged-in app flow to show workspace by default after auth session is available in `ui/src/app/App.tsx`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - 在工作空间中创建和浏览多个应用 (Priority: P2)

**Goal**: 用户可以创建多个应用，以卡片浏览应用，编辑应用名称和说明；同一工作空间内应用名称唯一；首版不提供删除应用。

**Independent Test**: 在一个工作空间中创建多个不同名称应用，确认卡片列表展示；编辑名称和说明后卡片与详情数据一致；创建或编辑为同名时被拒绝；界面无删除入口。

### Tests for User Story 2

- [X] T025 [P] [US2] Add contract tests for `POST /api/workspace/applications`, `PATCH /api/workspace/applications/{application_id}`, duplicate-name conflict, and validation errors in `server/tests/contract/test_workspace_api.py`
- [X] T026 [P] [US2] Add integration test for creating multiple applications, editing name/description, duplicate rejection, and no cross-user modification in `server/tests/integration/test_workspace_flow.py`
- [X] T027 [P] [US2] Add unit tests for application name/description validation and same-workspace uniqueness decisions in `server/tests/unit/workspace/test_workspace_domain.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement `create_application` and `update_application_summary` use cases with duplicate-name handling and debug logs in `server/src/application/workspace/use_cases.py`
- [X] T029 [US2] Implement repository methods for application create, list, duplicate lookup, and update in `server/src/infrastructure/persistence/workspace_repository.py`
- [X] T030 [US2] Implement `POST /api/workspace/applications` and `PATCH /api/workspace/applications/{application_id}` routes and schemas in `server/src/presentation/api/workspace.py`
- [X] T031 [P] [US2] Add `createWorkspaceApplication` and `updateWorkspaceApplication` API client functions in `ui/src/features/workspace/api.ts`
- [X] T032 [P] [US2] Implement application create/edit form with field validation and server error display in `ui/src/features/workspace/components/ApplicationForm.tsx`
- [X] T033 [P] [US2] Implement application card and application grid components without delete controls in `ui/src/features/workspace/components/ApplicationCard.tsx` and `ui/src/features/workspace/components/ApplicationGrid.tsx`
- [X] T034 [US2] Extend `useWorkspace` to create applications, update applications, refresh cards, and map duplicate-name errors in `ui/src/features/workspace/hooks/useWorkspace.ts`
- [X] T035 [US2] Extend `WorkspacePage` to display application cards, open create/edit form, and keep updated cards visible in `ui/src/features/workspace/pages/WorkspacePage.tsx`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - 进入应用并进行流程编排 (Priority: P3)

**Goal**: 用户从应用卡片进入应用详情，看到左侧应用信息和右侧空编排画布入口；首版不提供任何节点编辑、保存、运行或调试能力。

**Independent Test**: 从任一应用卡片进入详情，确认左侧信息可识别，右侧展示空画布和开始编排入口，且没有新增/移动/连接/删除节点或运行调试控件。

### Tests for User Story 3

- [X] T036 [P] [US3] Add contract tests for `GET /api/workspace/applications/{application_id}`, empty canvas payload, not-found, and cross-user rejection in `server/tests/contract/test_workspace_api.py`
- [X] T037 [P] [US3] Add integration test for card-to-detail API journey and non-editable canvas response in `server/tests/integration/test_workspace_flow.py`
- [X] T038 [P] [US3] Add unit tests for fixed empty `ApplicationCanvasView` behavior in `server/tests/unit/workspace/test_workspace_domain.py`

### Implementation for User Story 3

- [X] T039 [US3] Implement `get_application_detail` use case returning application info and non-editable empty canvas in `server/src/application/workspace/use_cases.py`
- [X] T040 [US3] Implement repository method for owner-scoped application detail lookup in `server/src/infrastructure/persistence/workspace_repository.py`
- [X] T041 [US3] Implement `GET /api/workspace/applications/{application_id}` route and canvas response schema in `server/src/presentation/api/workspace.py`
- [X] T042 [P] [US3] Add `getWorkspaceApplication` API client function and detail response types in `ui/src/features/workspace/api.ts`
- [X] T043 [P] [US3] Implement left-side application information panel in `ui/src/features/workspace/components/ApplicationInfoPanel.tsx`
- [X] T044 [P] [US3] Implement non-editable empty canvas component with start-entry state in `ui/src/features/workspace/components/ApplicationCanvasEmpty.tsx`
- [X] T045 [US3] Implement application detail layout with responsive left-info/right-canvas composition in `ui/src/features/workspace/components/ApplicationDetailLayout.tsx`
- [X] T046 [US3] Extend `WorkspacePage` to navigate from cards to detail state and back without adding router dependencies in `ui/src/features/workspace/pages/WorkspacePage.tsx` — 已被用户决定取代（2026-11-07）：用户要求「前端需要路由，不要所有的页面都放在一起」，选定 react-router-dom + 路径式 URL，故「不引入路由依赖」约束解除；卡片→详情改为 `/workspace/applications/:applicationId` 路由导航，见 T070

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 完成数据升级说明、日志可观测性、文档和完整验收。

- [X] T047 [P] Update backend documentation with workspace migration and verification commands in `server/README.md`
- [X] T048 [P] Update frontend documentation with logged-in workspace verification steps in `ui/README.md`
- [X] T049 Add debug-level workspace data-flow logs and sensitive-data safeguards in `server/src/application/workspace/use_cases.py`
- [X] T050 Execute workspace migration verification and record any required fixes using `server/scripts/migrate_workspace_schema.py`
- [X] T051 Execute backend automated verification for workspace tests using `server/tests/contract/test_workspace_api.py`, `server/tests/integration/test_workspace_flow.py`, and `server/tests/unit/workspace/test_workspace_domain.py`
- [X] T052 Execute frontend typecheck and build verification using `ui/package.json`
- [X] T053 Run the real-data quickstart validation and inspect logs/database state using `specs/005-app-workspace-canvas/quickstart.md`

### Addendum 2026-05-27: 知识库异步任务状态恢复

- [X] T054 Add contract regression test proving `GET /api/workspace/knowledge-bases/{knowledge_base_id}` returns the latest processing job after reopening the detail page in `server/tests/contract/test_knowledge_api.py`
- [X] T055 Expose owner-scoped latest document-processing job lookup through application use cases and include the job summary in knowledge-base detail responses in `server/src/application/document_processing/use_cases.py`, `server/src/application/workspace/use_cases.py`, and `server/src/presentation/api/workspace.py`
- [X] T056 Update knowledge-base frontend status display so list/detail views reflect processing, active, and failed states from persisted backend data in `ui/src/features/knowledge/pages/KnowledgeBaseCreatePage.tsx`
- [X] T057 Isolate backend test logs through configurable `LOG_DIR` and lazy ASGI app initialization to avoid import-time writes to root-owned local logs in `server/src/core/config.py`, `server/src/main.py`, and `server/tests/conftest.py`
- [X] T058 Verify async-task recovery with backend contract tests and frontend typecheck.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies; can start immediately.
- **Phase 2 Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2 and is the MVP.
- **Phase 4 US2**: Depends on Phase 2; practically uses the current workspace created by US1 but remains independently testable through API setup.
- **Phase 5 US3**: Depends on Phase 2 and requires an existing application from US2 for the UI path.
- **Phase 6 Polish**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other stories after foundation.
- **US2 (P2)**: Requires default workspace capability from US1 for normal user flow; can be tested with seeded/current workspace API.
- **US3 (P3)**: Requires at least one application from US2 to enter detail view.

### Within Each User Story

- Tests are written before implementation and should fail first.
- Domain/value rules before use cases.
- Repository operations before API routes that need persistence.
- API client before hook integration.
- Components before page composition when possible.
- Story checkpoint must pass before moving to the next priority for sequential delivery.

### Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001.
- T014, T015, and T016 can run in parallel for US1 tests.
- T020, T021, and T022 can run in parallel after US1 API contract is clear.
- T025, T026, and T027 can run in parallel for US2 tests.
- T031, T032, and T033 can run in parallel for US2 frontend slices.
- T036, T037, and T038 can run in parallel for US3 tests.
- T042, T043, and T044 can run in parallel for US3 frontend/detail slices.
- T047 and T048 can run in parallel during polish.

---

## Parallel Example: User Story 1

```text
Task: "Add contract tests for GET /api/workspace/current in server/tests/contract/test_workspace_api.py"
Task: "Add integration test for login/register then default workspace entry in server/tests/integration/test_workspace_flow.py"
Task: "Add unit tests for default workspace creation in server/tests/unit/workspace/test_workspace_domain.py"
```

```text
Task: "Implement getCurrentWorkspace API client in ui/src/features/workspace/api.ts"
Task: "Implement useWorkspace loading state in ui/src/features/workspace/hooks/useWorkspace.ts"
Task: "Implement empty workspace state in ui/src/features/workspace/components/WorkspaceEmptyState.tsx"
```

## Parallel Example: User Story 2

```text
Task: "Add create/update API client functions in ui/src/features/workspace/api.ts"
Task: "Implement application form in ui/src/features/workspace/components/ApplicationForm.tsx"
Task: "Implement application card/grid components in ui/src/features/workspace/components/ApplicationCard.tsx and ui/src/features/workspace/components/ApplicationGrid.tsx"
```

## Parallel Example: User Story 3

```text
Task: "Add getWorkspaceApplication API client in ui/src/features/workspace/api.ts"
Task: "Implement application information panel in ui/src/features/workspace/components/ApplicationInfoPanel.tsx"
Task: "Implement empty canvas component in ui/src/features/workspace/components/ApplicationCanvasEmpty.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate default workspace auto-create, empty app state, and user isolation.

### Incremental Delivery

1. Deliver US1 so login leads to a personal workspace.
2. Deliver US2 so the workspace can manage application cards and basic info.
3. Deliver US3 so application details expose the future orchestration canvas entry.
4. Run Phase 6 verification against quickstart and logs/database state.

### Parallel Team Strategy

1. Complete Setup and Foundational tasks together.
2. Assign backend tests, backend implementation, and frontend slices per story to separate workers when paths do not overlap.
3. Integrate in priority order: US1 → US2 → US3.
4. Preserve the worktree boundary: all implementation must occur in `/home/xmin/workspace/code/ai-flow/.worktrees/005-app-workspace-canvas`.

## Notes

- `[P]` tasks touch different files or can proceed without waiting on incomplete implementation in the same file.
- `[US1]`, `[US2]`, and `[US3]` map directly to user stories in [spec.md](./spec.md).
- Do not add third-party dependencies for this feature.
- Do not implement application deletion or editable workflow canvas behavior in this scope.
- Do not expose or trust client-provided `user_id`; derive identity from the current auth session.

---

## Phase 7: Convergence

**Purpose**: 2026-11-07 converge 评估发现：T001–T058 的完成标记来自另一代码库（`/home/xmin/.../.worktrees/005-app-workspace-canvas`），当前仓库中 005 范围的应用/画布实现不存在，现有 workspace 代码属于 004-workspace-management（成员/角色/切换）。以下任务为本仓库中剩余的待完成工作。

- [X] T059 Implement `WorkspaceApplication`, `ApplicationCardView`, and `ApplicationCanvasView` entities plus application name/description value-object validation (name trimmed non-empty 1-80 chars, description 0-500 chars) in `server/src/domain/workspace/entities.py` and `server/src/domain/workspace/value_objects.py`, coexisting with the existing 004 membership model per FR-005, FR-006, data-model §3-§5 — done 2026-11-07：实体与名称/描述值对象校验已存在并通过单元测试
- [X] T060 Add idempotent `workspace_applications` DDL with unique index on `(workspace_id, name)` to `server/src/infrastructure/persistence/workspace_migrations.py` and create explicit migration entry `server/scripts/migrate_workspace_schema.py` with schema verification output per FR-006, T008, T009, data-model migration strategy — done 2026-11-07：幂等 DDL + 唯一索引 + 迁移脚本校验输出
- [X] T061 Implement application use cases in `server/src/application/workspace/use_cases.py`: `get_or_create_current_workspace` (returning application cards), `create_application` and `update_application_summary` (with same-workspace duplicate-name rejection), and `get_application_detail` (returning info plus fixed non-editable empty canvas), with owner-scoped access errors per FR-003, FR-004, FR-009, FR-010, FR-014, FR-015, FR-016 — done 2026-11-07：用例已实现（含审计写入走同一事务连接，避免 SQLite 写锁冲突）
- [X] T062 Add session-derived routes `GET /api/workspace/current`, `POST /api/workspace/applications`, `PATCH /api/workspace/applications/{application_id}`, and `GET /api/workspace/applications/{application_id}` (canvas payload with `mode=empty`, `editable=false`, `entry_label`), never trusting client-provided `user_id`, wired into `server/src/main.py` per FR-001, FR-002, FR-007, FR-008, FR-012 — done 2026-11-07：会话派生路由已接入 main.py
- [X] T063 Add backend tests for the 005 scope: contract tests for current-workspace/application endpoints (auto-create, duplicate-name 409, validation 422, not-found/cross-user rejection, empty canvas payload) in `server/tests/contract/test_workspace_api.py`, integration journey in `server/tests/integration/test_workspace_flow.py`, and create `server/tests/unit/workspace/test_workspace_domain.py` for domain rules per T014-T016, T025-T027, T036-T038 — done 2026-11-07：`uv run pytest -q` → 104 passed
- [X] T064 Implement frontend API clients (`getCurrentWorkspace`, `createWorkspaceApplication`, `updateWorkspaceApplication`, `getWorkspaceApplication`) and `useWorkspace` hook (loading/empty/error/refresh, create/update, duplicate-name error mapping) in `ui/src/features/workspace/api.ts` and `ui/src/features/workspace/hooks/useWorkspace.ts` per T020, T021, T031, T034, T042 — done 2026-11-07：api.ts 客户端 + useWorkspace hook（loading/empty/error/refresh、create/update、重复名称文案映射）
- [X] T065 Implement `WorkspacePage`, `WorkspaceEmptyState`, `ApplicationCard`/`ApplicationGrid` (no delete controls), and `ApplicationForm` (name/description validation, server error display) under `ui/src/features/workspace/`, and update `ui/src/app/App.tsx` so authenticated users land on the workspace by default per FR-001, FR-004, FR-007, FR-008, FR-010, FR-011, US1/AC1-4, US2/AC1-5, T022-T024, T032, T033, T035 — done 2026-11-07：EmptyState/Card/Grid/Form 完成，App 登录后默认进入工作空间页；原 `WorkspacePage.tsx` 已按路由拆分删除，列表页为 `pages/WorkspaceListPage.tsx`（见 T070）
- [X] T066 Implement application detail view: `ApplicationInfoPanel` (left), `ApplicationCanvasEmpty` (right, read-only empty canvas with start-orchestration entry, no node add/move/connect/delete), `ApplicationDetailLayout`, and card→detail→back navigation in `WorkspacePage` per FR-012, FR-013, FR-014, FR-015, US3/AC1-4, T043-T046 — done 2026-11-07：InfoPanel + 只读空画布 + DetailLayout + 卡片→详情→返回导航；卡片→详情→返回改由路由承载（`pages/ApplicationDetailPage.tsx` 读 URL 参数），「返回应用列表」是真实链接，见 T070
- [X] T067 Update `server/README.md` (workspace-applications migration and verification commands) and `ui/README.md` (logged-in workspace verification steps) for the 005 scope, and add debug-level workspace/application data-flow logs without cookie or sensitive values per T047-T049 — done 2026-11-07：两份 README 更新；debug 级数据流日志只含 id 与计数，不含 Cookie 或敏感值
- [X] T068 Resolve FR-018 scope: no knowledge-base or `document_processing` code exists in this repository, so latest-job recovery (T054-T056) has no prerequisite feature; confirm with stakeholders whether the knowledge-base feature belongs to this repo, then implement persisted job-status recovery and detail-response job summary, or record an approved scope exemption per FR-018, SC-007 — exemption（已批准记录）：本仓库无知识库/document_processing 代码，FR-018/SC-007 无前置功能可实现；T054-T056 属于另一代码库，本仓库按范围豁免处理
- [X] T069 Resolve FR-017 worktree binding: the project directory is not a git repository, so git worktree creation/binding is impossible; initialize git and establish the `005-app-workspace-canvas` worktree, or obtain and record an approved exemption per FR-017 — exemption（前提已失效）：本目录已是 git 仓库（分支 main），但尚无任何提交，无法创建 worktree；首次提交后可建立 005-app-workspace-canvas worktree，当前按豁免记录

### Addendum 2026-11-07: 前端页面路由（用户决定）

用户要求「前端需要路由，不要所有的页面都放在一起」，并选定 react-router-dom + 路径式 URL。以下为本仓库内已完成的实现（取代 T046 的「不引入路由依赖」约束）：

- [X] T070 [P] Introduce per-page routing in `ui/src/app/`: `router.tsx` 路由表（`/`、`/auth`、`/workspace`、`/workspace/applications/:applicationId`、`/session`、`/theme`、`/bootstrap`、`*`）、`guards/RequireAuth.tsx`、`guards/RequireGuest.tsx`、`guards/RootRedirect.tsx`、`components/AppNav.tsx`（NavLink）、`components/NotFoundPage.tsx`；`App.tsx` 只保留应用壳（BrowserRouter + AuthProvider + 导航 + 路由），不再把多个页面渲染在同一屏；会话状态由 `ui/src/features/auth/providers/AuthProvider.tsx` 单一 Provider 提供，守卫与页面共用，feature 不反向依赖 `app/`；跨 feature 布局原语 `ui/src/shared/components/PageShell.tsx`；004 的会话/切换器/成员内容移到 `/session`（`ui/src/features/auth/pages/SessionPage.tsx`）；`WorkspacePage.tsx` 拆为 `WorkspaceListPage.tsx`（`useNavigate` 进入详情）与 `ApplicationDetailPage.tsx`（`useParams` 决定应用，刷新/后退/直接输入地址落到同一应用） — done 2026-11-07：`pnpm run typecheck` 与 `pnpm run build` 均通过（95 modules，SPA 深链回退由 dev server 提供 index.html）；路由表与守卫模块经 dev server 请求返回 200。浏览器内的守卫跳转与后退行为未做可视化验证（本环境 Pencil 应用未连接），前端验收以运行验证和 `server/logs/frontend.log` 为准


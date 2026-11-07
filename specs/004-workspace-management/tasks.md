# Tasks: 工作空间与成员管理

**Input**: Design documents from `/specs/004-workspace-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/workspace-api.md, quickstart.md

**Tests**: 后端必须包含单元测试、集成测试、契约测试；前端至少通过 typecheck 和页面运行/关键交互验证。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create workspace feature skeleton and align existing auth/UI types with planned integration points.

- [X] T001 Create workspace backend package directories and `__init__.py` files in `/home/xmin/workspace/code/ai-flow/server/src/domain/workspace/`, `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/`
- [X] T002 Create workspace frontend feature directories in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/`
- [X] T003 [P] Create placeholder workspace API contract test file in `/home/xmin/workspace/code/ai-flow/server/tests/contract/test_workspace_api.py`
- [X] T004 [P] Create placeholder workspace integration test file in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T005 [P] Create placeholder workspace unit test directory and file in `/home/xmin/workspace/code/ai-flow/server/tests/unit/workspace/test_workspace_rules.py`
- [X] T006 [P] Create frontend workspace API module stub in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/api.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain model, persistence schema, application ports, and app wiring required by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Define workspace domain entities `Workspace`, `WorkspaceMembership`, `WorkspaceRole`, `UserWorkspacePreference`, `WorkspaceAuditEvent` in `/home/xmin/workspace/code/ai-flow/server/src/domain/workspace/entities.py`
- [X] T008 Define workspace value objects and validators for role, workspace name, membership status, and duplicate/last-manager rule errors in `/home/xmin/workspace/code/ai-flow/server/src/domain/workspace/value_objects.py`
- [X] T009 Define workspace domain services for manager authorization, role transition validation, and last-manager protection in `/home/xmin/workspace/code/ai-flow/server/src/domain/workspace/services.py`
- [X] T010 Define `WorkspaceRepositoryPort` and DTO/query result protocols in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/ports.py`
- [X] T011 Implement SQLite workspace migration DDL, indexes, idempotent backfill helpers, and validation SQL helpers in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/workspace_migrations.py`
- [X] T012 Implement SQLite workspace repository with workspace, membership, preference, audit, and username lookup operations in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/workspace_repository.py`
- [X] T013 Wire workspace migrations/repository/use cases into application startup in `/home/xmin/workspace/code/ai-flow/server/src/main.py`
- [X] T014 Include workspace API router placeholder in `/home/xmin/workspace/code/ai-flow/server/src/main.py` and create router shell in `/home/xmin/workspace/code/ai-flow/server/src/presentation/api/workspace.py`
- [X] T015 Extend test app fixtures to initialize workspace repository and use cases in `/home/xmin/workspace/code/ai-flow/server/tests/conftest.py`

**Checkpoint**: Foundation ready. Domain, repository, migration, and route skeletons exist and user stories can be implemented.

---

## Phase 3: User Story 1 - 注册后自动拥有工作空间 (Priority: P1) MVP

**Goal**: New users and existing users always have a default workspace, manager membership, and current workspace context in auth/session responses.

**Independent Test**: Register a new user and verify exactly one default workspace, manager role, current workspace context, and session response workspace payload.

### Tests for User Story 1

- [X] T016 [P] [US1] Add auth contract assertions for workspace context in register/login/session/refresh responses in `/home/xmin/workspace/code/ai-flow/server/tests/contract/test_auth_api.py`
- [X] T017 [P] [US1] Add integration test for registration creating one default workspace and manager membership in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T018 [P] [US1] Add migration test for existing users receiving default workspace, manager membership, and preference in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T019 [P] [US1] Add unit tests for default workspace name and manager membership invariants in `/home/xmin/workspace/code/ai-flow/server/tests/unit/workspace/test_workspace_rules.py`

### Implementation for User Story 1

- [X] T020 [US1] Implement default workspace creation and existing-user backfill use cases in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T021 [US1] Add transactional user registration plus default workspace creation flow in `/home/xmin/workspace/code/ai-flow/server/src/application/auth/use_cases.py`
- [X] T022 [US1] Extend auth repository port to support transactional registration boundary or coordinated commit data needed by workspace creation in `/home/xmin/workspace/code/ai-flow/server/src/application/auth/ports.py`
- [X] T023 [US1] Update SQLite auth repository implementation for the registration transaction boundary in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/auth_repository.py`
- [X] T024 [US1] Extend `AuthSessionView` or response DTO with current workspace and available workspace summaries in `/home/xmin/workspace/code/ai-flow/server/src/domain/auth/entities.py`
- [X] T025 [US1] Serialize workspace context in auth responses in `/home/xmin/workspace/code/ai-flow/server/src/presentation/api/auth.py`
- [X] T026 [US1] Add debug/info/error logs for default workspace creation and registration rollback failures in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T027 [US1] Update frontend auth session response types to include workspace context in `/home/xmin/workspace/code/ai-flow/ui/src/features/auth/api.ts`
- [X] T028 [US1] Display current workspace summary in authenticated session panel in `/home/xmin/workspace/code/ai-flow/ui/src/features/auth/components/AuthSessionPanel.tsx`

**Checkpoint**: User Story 1 is independently functional and testable as MVP.

---

## Phase 4: User Story 2 - 工作空间数据完全隔离 (Priority: P1)

**Goal**: Every workspace-scoped read/write path uses current workspace context, denies unauthorized workspace access, and supports switching current workspace.

**Independent Test**: Create two users/workspaces, switch or attempt access across workspaces, and verify data/member views never leak between workspaces.

### Tests for User Story 2

- [X] T029 [P] [US2] Add contract tests for `GET /api/workspaces` and `POST /api/workspaces/current` in `/home/xmin/workspace/code/ai-flow/server/tests/contract/test_workspace_api.py`
- [X] T030 [P] [US2] Add integration test for current workspace preference persistence and fallback after membership removal in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T031 [P] [US2] Add integration test proving unauthorized workspace access returns explicit errors and no foreign workspace data in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`

### Implementation for User Story 2

- [X] T032 [US2] Implement current workspace resolution, list workspaces, switch workspace, and access-denied use cases in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T033 [US2] Implement `GET /api/workspaces` and `POST /api/workspaces/current` endpoints in `/home/xmin/workspace/code/ai-flow/server/src/presentation/api/workspace.py`
- [X] T034 [US2] Add workspace current/preference repository methods and unauthorized lookup protections in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/workspace_repository.py`
- [X] T035 [US2] Ensure auth session lookup resolves inaccessible previous workspace to another accessible workspace or empty state in `/home/xmin/workspace/code/ai-flow/server/src/application/auth/use_cases.py`
- [X] T036 [US2] Implement frontend workspace API functions for list and switch in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/api.ts`
- [X] T037 [US2] Implement `useWorkspaceSession` hook for current/available workspace state and switch action in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/hooks/useWorkspaceSession.ts`
- [X] T038 [US2] Implement `WorkspaceSwitcher` component with accessible loading, empty, and error states in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/components/WorkspaceSwitcher.tsx`
- [X] T039 [US2] Integrate workspace switcher into authenticated page without bypassing existing theme components in `/home/xmin/workspace/code/ai-flow/ui/src/features/auth/pages/AuthPage.tsx`

**Checkpoint**: User Stories 1 and 2 both work independently; workspace context is authoritative for all visible workspace data.

---

## Phase 5: User Story 3 - 管理工作空间成员 (Priority: P2)

**Goal**: Managers can add registered users by username and remove members; ordinary members cannot manage members.

**Independent Test**: Use manager and ordinary member accounts to add/remove members, verify membership list changes, access is revoked immediately, and permission errors are explicit.

### Tests for User Story 3

- [X] T040 [P] [US3] Add contract tests for list members, add member by username, remove member, duplicate member, and user-not-found responses in `/home/xmin/workspace/code/ai-flow/server/tests/contract/test_workspace_api.py`
- [X] T041 [P] [US3] Add integration test for manager adding/removing member and revoked member losing workspace access in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T042 [P] [US3] Add integration test for ordinary member receiving `WORKSPACE_MANAGER_REQUIRED` when adding or deleting members in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T043 [P] [US3] Add unit tests for manager authorization and duplicate membership rule in `/home/xmin/workspace/code/ai-flow/server/tests/unit/workspace/test_workspace_rules.py`

### Implementation for User Story 3

- [X] T044 [US3] Implement list members, add member by username, and remove member use cases with audit events in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T045 [US3] Implement `GET /api/workspaces/current/members`, `POST /api/workspaces/current/members`, and `DELETE /api/workspaces/current/members/{user_id}` in `/home/xmin/workspace/code/ai-flow/server/src/presentation/api/workspace.py`
- [X] T046 [US3] Add member list/add/remove repository methods and audit event persistence in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/workspace_repository.py`
- [X] T047 [US3] Add info/warning logs for member add/remove success, duplicate member, user-not-found, and member permission denial in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T048 [US3] Implement frontend workspace member API functions in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/api.ts`
- [X] T049 [US3] Implement `WorkspaceMembersPanel` component for listing, adding by username, removing members, and showing permission errors in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/components/WorkspaceMembersPanel.tsx`
- [X] T050 [US3] Render member management UI only for managers and read-only member list for ordinary members in `/home/xmin/workspace/code/ai-flow/ui/src/features/auth/pages/AuthPage.tsx`

**Checkpoint**: User Story 3 works independently after US1/US2 foundation; manager member management is functional and ordinary members are blocked.

---

## Phase 6: User Story 4 - 区分管理者与成员角色 (Priority: P2)

**Goal**: Role changes are workspace-specific, manager-only, and cannot remove the last manager.

**Independent Test**: Put the same user in two workspaces with different roles, verify permissions differ by workspace, allow valid role changes, and reject last-manager downgrade.

### Tests for User Story 4

- [X] T051 [P] [US4] Add contract tests for `PATCH /api/workspaces/current/members/{user_id}` success, invalid role, member-not-found, and last-manager protection in `/home/xmin/workspace/code/ai-flow/server/tests/contract/test_workspace_api.py`
- [X] T052 [P] [US4] Add integration test for same user having manager role in one workspace and member role in another workspace in `/home/xmin/workspace/code/ai-flow/server/tests/integration/test_workspace_flow.py`
- [X] T053 [P] [US4] Add unit tests for valid role transitions and last-manager downgrade protection in `/home/xmin/workspace/code/ai-flow/server/tests/unit/workspace/test_workspace_rules.py`

### Implementation for User Story 4

- [X] T054 [US4] Implement role change use case with manager-only authorization and last-manager protection in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T055 [US4] Implement `PATCH /api/workspaces/current/members/{user_id}` endpoint in `/home/xmin/workspace/code/ai-flow/server/src/presentation/api/workspace.py`
- [X] T056 [US4] Add repository method for atomic role update with last-manager validation support in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/workspace_repository.py`
- [X] T057 [US4] Add audit events and warning logs for role change success, invalid role, and last-manager protection in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`
- [X] T058 [US4] Add frontend role change API function in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/api.ts`
- [X] T059 [US4] Add role selector/actions for managers and protection error display in `/home/xmin/workspace/code/ai-flow/ui/src/features/workspace/components/WorkspaceMembersPanel.tsx`

**Checkpoint**: All user stories are independently functional, and role behavior is scoped per workspace.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Validation, cleanup, docs, and release-safety checks across all stories.

- [X] T060 [P] Update backend README with workspace migration and validation commands in `/home/xmin/workspace/code/ai-flow/server/README.md`
- [X] T061 [P] Update frontend README or feature notes with workspace UI validation steps in `/home/xmin/workspace/code/ai-flow/ui/README.md`
- [X] T062 Run backend targeted tests from quickstart and fix failures in `/home/xmin/workspace/code/ai-flow/server/tests/`
- [X] T063 Run frontend typecheck and fix failures in `/home/xmin/workspace/code/ai-flow/ui/src/`
- [X] T064 Run manual quickstart curl validation and confirm backend logs in `/home/xmin/workspace/code/ai-flow/server/logs/backend.log`
- [X] T065 Review generated workspace migrations for idempotency, rollback notes, and validation SQL coverage in `/home/xmin/workspace/code/ai-flow/server/src/infrastructure/persistence/workspace_migrations.py`
- [X] T066 Review final implementation for no sensitive log output and no unauthorized workspace data leakage in `/home/xmin/workspace/code/ai-flow/server/src/application/workspace/use_cases.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks every user story.
- **US1 (Phase 3)**: Depends on Foundational; MVP.
- **US2 (Phase 4)**: Depends on Foundational and uses US1 session/default workspace context.
- **US3 (Phase 5)**: Depends on US1 and US2 current workspace resolution.
- **US4 (Phase 6)**: Depends on US3 member management base.
- **Polish**: Depends on completed target user stories.

### User Story Dependencies

- **US1**: Required first for default workspace and session workspace context.
- **US2**: Requires workspace context and persistence from US1.
- **US3**: Requires current workspace resolution from US2.
- **US4**: Requires member management from US3.

### Parallel Opportunities

- Setup placeholder files T003-T006 can run in parallel.
- Test-writing tasks inside each user story can run in parallel before implementation.
- Backend API/UI work within US2 can split after use cases and contracts are stable.
- Frontend API/component tasks in US3 and US4 can run in parallel with backend implementation if contracts are fixed.

## Parallel Examples

### User Story 1

```text
Task: "T016 Add auth contract assertions in server/tests/contract/test_auth_api.py"
Task: "T017 Add registration integration test in server/tests/integration/test_workspace_flow.py"
Task: "T018 Add migration integration test in server/tests/integration/test_workspace_flow.py"
Task: "T019 Add domain invariant unit tests in server/tests/unit/workspace/test_workspace_rules.py"
```

### User Story 2

```text
Task: "T029 Add workspace list/switch contract tests in server/tests/contract/test_workspace_api.py"
Task: "T030 Add preference fallback integration test in server/tests/integration/test_workspace_flow.py"
Task: "T036 Implement frontend workspace API functions in ui/src/features/workspace/api.ts"
Task: "T038 Implement WorkspaceSwitcher in ui/src/features/workspace/components/WorkspaceSwitcher.tsx"
```

### User Story 3

```text
Task: "T040 Add member management contract tests in server/tests/contract/test_workspace_api.py"
Task: "T041 Add manager add/remove integration test in server/tests/integration/test_workspace_flow.py"
Task: "T048 Implement frontend member API functions in ui/src/features/workspace/api.ts"
Task: "T049 Implement WorkspaceMembersPanel in ui/src/features/workspace/components/WorkspaceMembersPanel.tsx"
```

### User Story 4

```text
Task: "T051 Add role change contract tests in server/tests/contract/test_workspace_api.py"
Task: "T052 Add per-workspace role integration test in server/tests/integration/test_workspace_flow.py"
Task: "T058 Add frontend role change API function in ui/src/features/workspace/api.ts"
Task: "T059 Add role selector/actions in ui/src/features/workspace/components/WorkspaceMembersPanel.tsx"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 Setup.
2. Complete Phase 2 Foundational schema/domain/repository wiring.
3. Complete Phase 3 US1.
4. Stop and validate: registration creates default workspace, session response includes current workspace, migration creates default workspace for existing users.

### Incremental Delivery

1. Deliver US1 as MVP.
2. Add US2 for workspace switching and isolation.
3. Add US3 for add/remove member management.
4. Add US4 for role mutation and last-manager protection.
5. Run Final Phase validation before marking the feature complete.

### Validation Commands

```bash
cd server
uv run pytest tests/contract/test_auth_api.py tests/contract/test_workspace_api.py tests/integration/test_workspace_flow.py tests/unit/workspace
```

```bash
cd ui
pnpm run typecheck
```

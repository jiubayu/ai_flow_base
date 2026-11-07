# Tasks: 邮箱验证码与密码认证

**Input**: Design documents from `/specs/003-email-password-auth/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 本特性显式要求后端单元/契约/集成测试，以及前端 `typecheck`、`build` 和浏览器真实链路验证，因此任务中包含测试与验证项。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- 后端代码位于 `server/src/`
- 后端测试位于 `server/tests/`
- 前端代码位于 `ui/src/`
- 规划与验收文档位于 `specs/003-email-password-auth/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 准备认证功能所需的本地配置入口、迁移脚本入口和测试环境默认值

- [X] T001 更新 `server/.env.example` 和 `ui/.env.example`，补充认证 TTL、Cookie、SMTP 与前端认证入口所需配置占位
- [X] T002 创建 `server/scripts/migrate_auth_schema.py`，提供认证 SQLite schema 的幂等迁移命令入口
- [X] T003 [P] 更新 `server/tests/conftest.py`，补充认证测试环境默认配置、短 TTL 和可替换邮件发送依赖的 fixture

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有用户故事共享的认证域模型、基础设施、路由入口和前端共享会话能力

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 创建 `server/src/domain/auth/entities.py`、`server/src/domain/auth/value_objects.py` 和 `server/src/domain/auth/services.py`，定义用户、验证码挑战、会话、刷新资格与审计事件领域模型
- [X] T005 [P] 创建 `server/src/application/auth/ports.py` 和 `server/src/application/auth/services.py`，定义认证仓储、邮件发送、时间与会话管理端口
- [X] T006 [P] 创建 `server/src/infrastructure/persistence/auth_models.py` 和 `server/src/infrastructure/persistence/auth_repository.py`，实现认证表映射与仓储骨架
- [X] T007 [P] 创建 `server/src/infrastructure/security/password_hasher.py` 和 `server/src/infrastructure/security/cookie_session_manager.py`，实现 `scrypt` 密码散列与 Cookie 会话签发/清理骨架
- [X] T008 [P] 创建 `server/src/infrastructure/messaging/smtp_email_sender.py` 和 `server/src/infrastructure/persistence/auth_migrations.py`，实现 SMTP 适配器与幂等迁移逻辑
- [X] T009 更新 `server/src/application/auth/use_cases.py`、`server/src/presentation/api/auth.py` 和 `server/src/main.py`，接入认证用例装配、认证路由和应用状态依赖注入
- [X] T010 [P] 更新 `ui/src/shared/lib/http.ts`，让认证相关请求统一支持 `credentials: "include"` 与标准化错误处理
- [X] T011 [P] 创建 `ui/src/features/auth/api.ts` 和 `ui/src/features/auth/hooks/useAuthSession.ts`，建立认证 API 客户端与共享会话状态骨架
- [X] T012 创建 `ui/src/features/auth/pages/AuthPage.tsx` 和更新 `ui/src/app/App.tsx`，挂载认证 feature 页面入口与基础布局

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 通过邮箱注册账号 (Priority: P1) 🎯 MVP

**Goal**: 让访客完成验证码发送、限流提示、邮箱校验、密码设置和注册成功后自动登录

**Independent Test**: 运行 `server/tests/contract/test_auth_api.py` 与 `server/tests/integration/test_auth_flow.py` 中的 US1 用例，并在浏览器中完成一次“发送验证码 → 注册成功自动登录”的真实链路验证

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] 在 `server/tests/contract/test_auth_api.py` 中添加 `POST /api/auth/email-code` 与 `POST /api/auth/register` 的契约测试
- [X] T014 [P] [US1] 在 `server/tests/integration/test_auth_flow.py` 中添加验证码发送、双重限流、错误验证码和注册自动登录的集成测试

### Implementation for User Story 1

- [X] T015 [US1] 在 `server/src/application/auth/use_cases.py` 和 `server/src/infrastructure/persistence/auth_repository.py` 中实现验证码发送、单邮箱单有效挑战、双重限流和审计记录逻辑
- [X] T016 [US1] 在 `server/src/presentation/api/auth.py` 中实现 `POST /api/auth/email-code` 与 `POST /api/auth/register`，覆盖校验、错误码、Cookie 写入和日志上下文
- [X] T017 [P] [US1] 在 `ui/src/features/auth/api.ts` 和 `ui/src/features/auth/hooks/useAuthSession.ts` 中实现发送验证码与注册接口调用、注册成功后的会话写回
- [X] T018 [P] [US1] 创建 `ui/src/features/auth/components/RegisterForm.tsx`，实现邮箱输入、验证码发送、密码校验和限流提示 UI
- [X] T019 [US1] 更新 `ui/src/features/auth/pages/AuthPage.tsx` 和 `ui/src/app/App.tsx`，接通注册流程并在注册成功后展示已登录状态

**Checkpoint**: User Story 1 完成后，访客应能独立完成邮箱注册并自动进入已登录状态

---

## Phase 4: User Story 2 - 使用邮箱和密码登录 (Priority: P1)

**Goal**: 让已注册用户通过邮箱密码登录，并在页面刷新或后续请求中保持当前浏览器会话

**Independent Test**: 运行 `server/tests/contract/test_auth_api.py` 与 `server/tests/integration/test_auth_flow.py` 中的 US2 用例，并确认浏览器刷新页面后仍可识别当前登录用户

### Tests for User Story 2 ⚠️

- [X] T020 [P] [US2] 在 `server/tests/contract/test_auth_api.py` 中添加 `POST /api/auth/login` 与 `GET /api/auth/session` 的契约测试
- [X] T021 [P] [US2] 在 `server/tests/integration/test_auth_flow.py` 中添加密码登录、错误凭证和当前浏览器会话恢复的集成测试

### Implementation for User Story 2

- [X] T022 [US2] 在 `server/src/application/auth/use_cases.py` 和 `server/src/infrastructure/persistence/auth_repository.py` 中实现密码校验、当前会话读取和最近登录状态更新
- [X] T023 [US2] 在 `server/src/presentation/api/auth.py` 中实现 `POST /api/auth/login` 与 `GET /api/auth/session`，返回当前用户摘要和会话过期时间
- [X] T024 [P] [US2] 在 `ui/src/features/auth/api.ts` 和 `ui/src/features/auth/hooks/useAuthSession.ts` 中实现登录请求、当前会话查询和页面初始化恢复逻辑
- [X] T025 [P] [US2] 创建 `ui/src/features/auth/components/LoginForm.tsx` 和 `ui/src/features/auth/components/AuthSessionPanel.tsx`，实现登录表单和当前登录态展示
- [X] T026 [US2] 更新 `ui/src/features/auth/pages/AuthPage.tsx` 和 `ui/src/app/App.tsx`，支持登录/已登录双态切换与页面刷新后的会话恢复

**Checkpoint**: User Story 2 完成后，已注册用户应能独立登录并在刷新页面后保持当前浏览器会话

---

## Phase 5: User Story 3 - 维持、刷新与退出登录状态 (Priority: P2)

**Goal**: 让当前浏览器会话在 access 过期后可安全刷新，并在登出后彻底失效当前浏览器会话

**Independent Test**: 运行 `server/tests/contract/test_auth_api.py` 与 `server/tests/integration/test_auth_flow.py` 中的 US3 用例，并在浏览器中验证“过期后刷新恢复”“登出后当前浏览器失效、其他浏览器不受影响”

### Tests for User Story 3 ⚠️

- [X] T027 [P] [US3] 在 `server/tests/contract/test_auth_api.py` 中添加 `POST /api/auth/refresh` 与 `POST /api/auth/logout` 的契约测试
- [X] T028 [P] [US3] 在 `server/tests/integration/test_auth_flow.py` 中添加 access 过期刷新、refresh 轮换复用失败和当前浏览器登出的集成测试

### Implementation for User Story 3

- [X] T029 [US3] 在 `server/src/application/auth/use_cases.py` 和 `server/src/infrastructure/security/cookie_session_manager.py` 中实现 refresh 一次性轮换、当前浏览器会话撤销和登出清理逻辑
- [X] T030 [US3] 在 `server/src/presentation/api/auth.py` 中实现 `POST /api/auth/refresh` 与 `POST /api/auth/logout`，覆盖 Cookie 轮换、Cookie 清理与失败日志
- [X] T031 [P] [US3] 在 `ui/src/features/auth/api.ts` 和 `ui/src/features/auth/hooks/useAuthSession.ts` 中实现刷新、登出、会话过期后的自动恢复与失败回退
- [X] T032 [US3] 更新 `ui/src/features/auth/components/AuthSessionPanel.tsx` 和 `ui/src/features/auth/pages/AuthPage.tsx`，提供刷新状态提示、登出入口和重新登录提示

**Checkpoint**: User Story 3 完成后，当前浏览器会话应支持自动刷新与显式登出，且旧刷新资格不可复用

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 完成跨故事测试、文档、构建与真实链路验收

- [X] T033 [P] 在 `server/tests/unit/auth/test_password_hasher.py`、`server/tests/unit/auth/test_code_service.py` 和 `server/tests/unit/auth/test_session_rotation.py` 中补齐密码散列、验证码限流和刷新轮换单元测试
- [X] T034 [P] 更新 `server/README.md`、`ui/README.md` 和 `specs/003-email-password-auth/quickstart.md`，补充迁移执行、SMTP 配置、Cookie 验证与失败恢复说明
- [X] T035 [P] 依据 `specs/003-email-password-auth/quickstart.md` 运行并修正 `server/tests/contract/test_auth_api.py` 与 `server/tests/integration/test_auth_flow.py` 覆盖的后端认证链路
- [X] T036 [P] 依据 `ui/package.json` 运行 `pnpm run typecheck` 与 `pnpm run build`，修正 `ui/src/features/auth/` 和 `ui/src/shared/lib/http.ts` 的最终前端问题
- [X] T037 在 `specs/003-email-password-auth/quickstart.md` 中执行浏览器手工验收清单，确认验证码、登录、刷新、当前浏览器登出和日志检查全部通过

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: 无依赖，可立即开始
- **Phase 2: Foundational**: 依赖 Setup 完成，阻塞所有用户故事
- **Phase 3: User Story 1**: 依赖 Foundational 完成，是 MVP 的最小交付范围
- **Phase 4: User Story 2**: 依赖 Foundational 完成；建议在 US1 跑通后继续，以复用已完成的用户与会话基础能力
- **Phase 5: User Story 3**: 依赖 Foundational 和 US2 完成；因为刷新/登出建立在已存在的登录会话上
- **Phase 6: Polish**: 依赖所有目标用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: 仅依赖 Foundational，可独立交付注册与自动登录 MVP
- **User Story 2 (P1)**: 依赖 Foundational；实现时会复用 US1 的用户与会话模型，但仍可独立验证登录与会话恢复
- **User Story 3 (P2)**: 依赖 US2 已产生稳定会话能力，之后才能独立验证刷新与当前浏览器登出

### Within Each User Story

- 先补测试，再实现后端用例与 API，再接通前端 API 与页面
- 后端用例/仓储逻辑先于前端页面接线
- 当前用户故事的独立测试通过后再进入下一故事

### Parallel Opportunities

- `T003`、`T006`、`T007`、`T008`、`T010`、`T011` 可在前两阶段并行
- `T013` 与 `T014` 可并行；`T017` 与 `T018` 可并行
- `T020` 与 `T021` 可并行；`T024` 与 `T025` 可并行
- `T027` 与 `T028` 可并行；`T031` 可与后端刷新接口开发后半段并行准备前端状态处理
- `T033`、`T034`、`T035`、`T036` 可在全部功能完成后并行推进

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 test tasks together:
Task: "Add contract coverage in server/tests/contract/test_auth_api.py"
Task: "Add integration coverage in server/tests/integration/test_auth_flow.py"

# Launch User Story 1 frontend tasks together after backend API shape is settled:
Task: "Implement register/request-code API calls in ui/src/features/auth/api.ts and ui/src/features/auth/hooks/useAuthSession.ts"
Task: "Build register form UI in ui/src/features/auth/components/RegisterForm.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch User Story 2 frontend tasks together:
Task: "Implement login/session API methods in ui/src/features/auth/api.ts and ui/src/features/auth/hooks/useAuthSession.ts"
Task: "Build login form and authenticated session panel in ui/src/features/auth/components/LoginForm.tsx and ui/src/features/auth/components/AuthSessionPanel.tsx"
```

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification tasks together:
Task: "Add contract coverage in server/tests/contract/test_auth_api.py"
Task: "Add integration coverage in server/tests/integration/test_auth_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. 运行 `T035` 的后端链路验证与 `T036` 的前端构建检查
5. 执行 `T037` 的注册真实链路验收后再决定是否继续

### Incremental Delivery

1. Setup + Foundational 完成后，先交付 US1 作为注册 MVP
2. 叠加 US2，补齐邮箱密码登录与浏览器会话恢复
3. 最后完成 US3，补齐刷新轮换与当前浏览器登出
4. 每完成一个故事，都先跑对应测试和手工验收，再进入下一阶段

### Parallel Team Strategy

1. 一名开发者完成 Setup + Foundational
2. Foundation 完成后：
   - 开发者 A：推进 US1 后端与前端注册链路
   - 开发者 B：在 US1 稳定后推进 US2 登录与当前会话恢复
   - 开发者 C：在 US2 稳定后推进 US3 刷新与登出链路
3. 收尾阶段由多人并行处理单元测试、文档与全链路验证

---

## Notes

- `[P]` 任务表示低耦合、不同文件、适合并行处理
- `[US1]`、`[US2]`、`[US3]` 与规格中的用户故事一一对应
- 所有数据库变更必须通过 `server/scripts/migrate_auth_schema.py` 与 `server/src/infrastructure/persistence/auth_migrations.py` 落地，不允许只改模型不交付迁移
- 浏览器自动携带凭证依赖 `credentials: "include"` 与后端 Cookie 配置，任何一侧缺失都会导致故事验收失败

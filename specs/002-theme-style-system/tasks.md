# Tasks: 项目主题样式系统

**Input**: Design documents from `/specs/002-theme-style-system/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 本特性未显式要求 TDD 或新增组件级自动化测试任务；验收通过 `ui/package.json` 中的 `typecheck`、`build` 命令，以及 `specs/002-theme-style-system/quickstart.md` 定义的页面运行与人工检查完成。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- 前端工程位于 `ui/`
- 共享主题与组件位于 `ui/src/shared/`
- 功能展示页位于 `ui/src/features/theme-showcase/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 为主题系统和 shadcn/ui 封装准备最小基础设施

- [x] T001 更新 `ui/package.json` 和 `ui/pnpm-lock.yaml`，添加已批准的 shadcn/ui 最小依赖集合
- [x] T002 创建 `ui/components.json` 和 `ui/src/shared/lib/utils.ts`，提供 shadcn/ui 注册配置与 class 合并工具
- [x] T003 更新 `ui/tsconfig.json` 和 `ui/vite.config.ts`，为 `@/` 路径别名和共享组件封装提供解析支持

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有用户故事共用的主题语义、样式入口和展示骨架

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 创建 `ui/src/shared/styles/tokens.css`，定义文本、背景、边框、强调、状态、圆角、阴影、间距、字号语义 token
- [x] T005 [P] 更新 `ui/tailwind.config.ts`，将语义 token 映射到 Tailwind theme 扩展
- [x] T006 [P] 创建 `ui/src/shared/styles/components.css`，沉淀共享 surface、typography 和 interaction-state 样式原语
- [x] T007 更新 `ui/src/shared/styles/index.css`，接入 `tokens.css` 和 `components.css` 并重设全局页面底色、字体和根布局
- [x] T008 [P] 创建 `ui/src/shared/components/theme/theme-tokens.ts`，维护主题 token 分组元数据供展示页与文档复用
- [x] T009 [P] 创建 `ui/src/features/theme-showcase/components/ThemeShowcaseShell.tsx` 和 `ui/src/features/theme-showcase/pages/ThemeShowcasePage.tsx`，搭好主题展示页面骨架

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 建立统一主题基线 (Priority: P1) 🎯 MVP

**Goal**: 建立全局主题基线，并让现有页面和共享卡片组件接入统一视觉语义

**Independent Test**: 启动前端后，开发者可在主题展示区和现有 bootstrap 页面中确认文本、背景、边框、阴影、圆角与状态色来自统一 token，而非局部硬编码

### Implementation for User Story 1

- [x] T010 [P] [US1] 创建 `ui/src/features/theme-showcase/components/ThemeTokenGallery.tsx`，展示主题 token 分类与语义用途
- [x] T011 [P] [US1] 创建 `ui/src/features/theme-showcase/components/SurfacePreview.tsx`，展示页面、面板、浮层和可点击项的层级差异
- [x] T012 [US1] 重构 `ui/src/shared/components/StatusCard.tsx`，改为消费统一的 surface、text 和 accent 语义类
- [x] T013 [US1] 重构 `ui/src/features/bootstrap-status/components/BootstrapStatusPanel.tsx`，替换 `slate`、`red` 等硬编码状态样式为语义类
- [x] T014 [US1] 更新 `ui/src/app/App.tsx`，用主题化页面壳承载现有 bootstrap 内容并挂载 `ThemeShowcasePage`
- [x] T015 [US1] 更新 `ui/src/features/theme-showcase/pages/ThemeShowcasePage.tsx`，整合 `ThemeTokenGallery` 与 `SurfacePreview` 形成主题基线展示

**Checkpoint**: User Story 1 应可独立演示统一主题基线，且现有首页已完成最小接入

---

## Phase 4: User Story 2 - 复用基础组件样式 (Priority: P2)

**Goal**: 提供可复用的基础组件与状态矩阵，并在展示页和现有模块中证明其可用性

**Independent Test**: 启动前端后，主题展示页可同时展示按钮、输入框、卡片、标签、导航项、筛选项、空态容器的默认态与交互态，且现有模块已复用至少一部分共享组件

### Implementation for User Story 2

- [x] T016 [P] [US2] 创建 `ui/src/shared/components/ui/button.tsx` 和 `ui/src/shared/components/ui/input.tsx`，封装基于主题 token 的按钮与输入框
- [x] T017 [P] [US2] 创建 `ui/src/shared/components/ui/card.tsx` 和 `ui/src/shared/components/ui/badge.tsx`，封装基于主题 token 的卡片与标签
- [x] T018 [P] [US2] 创建 `ui/src/shared/components/theme/NavItem.tsx`、`ui/src/shared/components/theme/FilterChip.tsx` 和 `ui/src/shared/components/theme/EmptyState.tsx`
- [x] T019 [US2] 创建 `ui/src/features/theme-showcase/components/ComponentStateShowcase.tsx`，展示基础组件的默认、悬停、聚焦、选中、禁用状态
- [x] T020 [US2] 更新 `ui/src/shared/components/StatusCard.tsx` 和 `ui/src/features/bootstrap-status/components/BootstrapStatusPanel.tsx`，接入共享 button/card/badge 原语
- [x] T021 [US2] 更新 `ui/src/features/theme-showcase/pages/ThemeShowcasePage.tsx`，整合 `ComponentStateShowcase`、导航项、筛选项和空态示例

**Checkpoint**: User Story 2 完成后，基础组件样式应可被真实页面与展示页共同复用

---

## Phase 5: User Story 3 - 支撑主题化扩展与验收 (Priority: P3)

**Goal**: 提供主题扩展准则、典型工作台式布局样例和评审入口，支撑后续扩展与验收

**Independent Test**: 团队成员可仅通过主题展示页、主题说明和现有接入页面，判断一个新页面是否正确复用主题 token 与基础组件样式

### Implementation for User Story 3

- [x] T022 [P] [US3] 创建 `ui/src/features/theme-showcase/components/WorkbenchPreview.tsx`，展示顶部导航、筛选栏、卡片网格和列表信息块的组合布局
- [x] T023 [P] [US3] 创建 `ui/src/shared/styles/theme-guidelines.md`，说明 token 命名、允许扩展方式和禁止的硬编码模式
- [x] T024 [US3] 创建 `ui/src/features/theme-showcase/components/ThemeAuditChecklist.tsx`，把 token 使用、状态区分和层级检查项显式展示给评审者
- [x] T025 [US3] 更新 `ui/src/features/theme-showcase/pages/ThemeShowcasePage.tsx`，整合 `WorkbenchPreview` 与 `ThemeAuditChecklist`
- [x] T026 [US3] 更新 `ui/README.md`，补充主题入口、展示页访问方式和新增组件时的扩展流程

**Checkpoint**: User Story 3 完成后，主题系统应具备清晰的扩展边界和验收入口

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 完成全局验证、文档对齐和收尾修正

- [x] T027 [P] 依据 `ui/package.json` 运行 `pnpm run typecheck` 与 `pnpm run build`，修复 `ui/src/` 下的最终类型与构建问题
- [x] T028 [P] 按照 `specs/002-theme-style-system/quickstart.md` 和 `specs/002-theme-style-system/contracts/theme-style-contract.md` 完成页面运行、响应式和交互态人工验收

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: 无依赖，可立即开始
- **Phase 2: Foundational**: 依赖 Setup 完成，阻塞所有用户故事
- **Phase 3: User Story 1**: 依赖 Foundational 完成，是 MVP 的最小交付范围
- **Phase 4: User Story 2**: 依赖 Foundational 完成；可与 US1 并行推进，但更推荐在 US1 基线稳定后接入现有页面
- **Phase 5: User Story 3**: 依赖 Foundational 完成；为得到更稳定的验收面，建议在 US1、US2 基本完成后收口
- **Phase 6: Polish**: 依赖所有目标用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: 仅依赖 Foundational，可独立交付主题基线
- **User Story 2 (P2)**: 仅依赖 Foundational，可独立交付基础组件体系
- **User Story 3 (P3)**: 依赖 Foundational；为了让审计与工作台样例更完整，建议在 US1、US2 可运行后执行

### Within Each User Story

- 先补齐展示/元数据组件，再改造共享组件与现有页面
- 共享组件封装先于真实页面接入
- 展示页整合应放在每个用户故事的最后一项，用于形成独立验收面

### Parallel Opportunities

- `T005`、`T006`、`T008`、`T009` 可在 Foundational 阶段并行
- `T010` 与 `T011` 可并行；`T016`、`T017`、`T018` 可并行；`T022` 与 `T023` 可并行
- `T027` 与 `T028` 可在所有实现任务完成后并行执行

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 showcase building blocks together:
Task: "Create ui/src/features/theme-showcase/components/ThemeTokenGallery.tsx"
Task: "Create ui/src/features/theme-showcase/components/SurfacePreview.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch User Story 2 shared component wrappers together:
Task: "Create ui/src/shared/components/ui/button.tsx and ui/src/shared/components/ui/input.tsx"
Task: "Create ui/src/shared/components/ui/card.tsx and ui/src/shared/components/ui/badge.tsx"
Task: "Create ui/src/shared/components/theme/NavItem.tsx, ui/src/shared/components/theme/FilterChip.tsx and ui/src/shared/components/theme/EmptyState.tsx"
```

## Parallel Example: User Story 3

```bash
# Launch User Story 3 audit artifacts together:
Task: "Create ui/src/features/theme-showcase/components/WorkbenchPreview.tsx"
Task: "Create ui/src/shared/styles/theme-guidelines.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. 运行 `T027` 的类型/构建检查，并执行 `T028` 的主题基线人工验收
5. 在主题基线稳定后再继续基础组件体系

### Incremental Delivery

1. Setup + Foundational 完成后，先交付 US1 作为统一主题基线
2. 叠加 US2，把主题落到基础组件体系并接入真实页面
3. 最后完成 US3，补齐工作台式组合样例、扩展规则和评审入口

### Parallel Team Strategy

1. 一名开发者完成 Setup + Foundational
2. Foundation 完成后：
   - 开发者 A：推进 US1 的主题基线和现有页面迁移
   - 开发者 B：推进 US2 的基础组件封装
   - 开发者 C：在 US1/US2 稳定后推进 US3 的验收与扩展规则

---

## Notes

- `[P]` 任务表示不同文件、低耦合、可并行执行
- `[US1]`、`[US2]`、`[US3]` 与规格中的用户故事一一对应
- 本次不单独生成组件自动化测试任务；验收重心在构建校验与页面运行验证
- 若实现阶段引入超出 shadcn/ui 最小集合之外的新依赖，必须先获得用户批准

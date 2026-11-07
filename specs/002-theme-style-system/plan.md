# Implementation Plan: 项目主题样式系统

**Branch**: `002-theme-style-system` | **Date**: 2026-05-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-theme-style-system/spec.md`

## Summary

在现有 `ui` 工程内建立统一主题样式系统，以全局语义化 token 为源，收敛文本、背景、边框、阴影、圆角、间距和状态色，抽象 AI-Flow 风格的轻量层级与柔和圆角，并将这些主题能力落到基础组件样式与一个可验收的主题展示页面。实现优先复用现有 React + Tailwind CSS + 全局样式结构，并在已获批准的前提下允许引入 shadcn/ui 作为基础组件承载层。

## Technical Context

**Language/Version**: TypeScript 5.x，CSS，React 18，Vite 5

**Primary Dependencies**: React，React DOM，Tailwind CSS 3，Vite，shadcn/ui（已获用户批准，可按需引入其组件依赖）

**Storage**: N/A（主题定义与组件样式保存在版本库中的样式与前端源码文件）

**Testing**: `pnpm run typecheck`，`pnpm run build`，前端手工页面运行验证，浏览器界面与状态展示验收

**Target Platform**: 桌面优先的现代浏览器开发环境，需兼容移动端基础浏览

**Project Type**: 单前端工程内的主题系统与共享 UI 基建能力

**Performance Goals**: 主题接入后首页与主题展示页在本地开发环境中保持即时渲染；主题切换和交互状态反馈应在一次用户交互内可感知完成；不因主题系统引入明显布局抖动

**Constraints**: 必须遵守前端 feature-based 结构；样式必须通过主题系统统一管理；新增依赖仅限已获批准的 shadcn/ui 相关最小集合；不得大量保留硬编码颜色；必须兼容现有 Tailwind 配置与共享样式入口；前端改动至少通过运行页面、关键交互和浏览器日志验证

**Scale/Scope**: 覆盖 1 套全局主题 token、1 个共享主题接入入口、1 组基础组件样式规范、1 个主题验收展示页，以及对现有首页/共享组件的最小迁移接入

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`：虽然 [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) 仍是占位模板，当前治理以 [AGENTS.md](../../AGENTS.md) 为准。
- `PASS`：本特性限定在前端 `ui` 工程内，遵守 React + Tailwind CSS + feature-based 结构；用户已明确批准可使用 shadcn/ui，因此组件层可在该边界内扩展。
- `PASS`：主题能力会通过全局主题入口和共享组件收敛，不允许单页绕过组件体系或散落页面级硬编码视觉规则。
- `PASS`：本次不涉及后端、数据库和数据迁移，无 schema 风险与回滚阻断项。
- `PASS`：验收路径符合 AGENTS 要求，包含类型检查、构建验证、前端运行验证和关键交互/视觉检查。

### Post-Design Constitution Check

- `PASS`：设计产物已将主题 token、组件状态矩阵、展示页与验收步骤限定在 `ui/src/shared` 和 `ui/src/features/theme-showcase` 等前端目录内，符合 feature-based 和共享样式边界。
- `PASS`：设计允许按需引入 shadcn/ui 作为基础组件承载层，但主题语义仍以项目级 token 为唯一事实来源，避免把视觉规范绑定为第三方默认样式。
- `PASS`：设计将验证方式明确为 `typecheck`、`build`、页面运行和浏览器人工检查，满足“不得只凭代码改动判断完成”的要求。

## Project Structure

### Documentation (this feature)

```text
specs/002-theme-style-system/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── theme-style-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
ui/
├── package.json
├── tailwind.config.ts
├── src/
│   ├── app/
│   │   └── App.tsx
│   ├── features/
│   │   ├── bootstrap-status/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── api.ts
│   │   └── theme-showcase/
│   │       ├── components/
│   │       └── pages/
│   ├── shared/
│   │   ├── components/
│   │   │   ├── StatusCard.tsx
│   │   │   ├── ui/
│   │   │   └── theme/
│   │   ├── lib/
│   │   └── styles/
│   │       ├── index.css
│   │       ├── tokens.css
│   │       └── components.css
│   └── main.tsx
└── public/
```

**Structure Decision**: 采用单前端工程内的共享主题方案。全局 token 与基础组件样式收敛到 `ui/src/shared/styles/` 和 `ui/src/shared/components/`，其中 `shared/components/ui/` 可承载 shadcn/ui 组件封装，`shared/components/theme/` 承载纯主题展示与辅助封装；主题验收示例作为独立 feature 放在 `ui/src/features/theme-showcase/`，同时对现有 `bootstrap-status` 页面做最小接入验证，避免把主题实现散落在 `app` 层或业务 feature 内。

## Complexity Tracking

无宪章违规项，无需复杂度豁免。

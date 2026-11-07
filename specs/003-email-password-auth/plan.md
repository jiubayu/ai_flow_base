# Implementation Plan: 邮箱验证码与密码认证

**Branch**: `003-email-password-auth` | **Date**: 2026-05-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-email-password-auth/spec.md`

## Summary

在现有 `server + ui` 骨架中新增认证垂直切片：后端以 DDD + 整洁架构补齐邮箱验证码发送、邮箱密码注册、登录、当前浏览器会话登出、自动凭证续期与审计日志；前端新增 `auth` feature，使用浏览器自动携带的 Cookie 会话完成注册/登录/会话刷新与当前登录态展示。实现优先复用现有 FastAPI、React、共享 HTTP 工具和 SQLite 本地运行环境，不新增未批准第三方依赖；密码散列、邮件发送与会话刷新采用标准库与现有基础设施完成，数据库变更通过显式迁移脚本交付。

## Technical Context

**Language/Version**: Python 3.11，TypeScript 5.x，React 18，Vite 5

**Primary Dependencies**: FastAPI，Pydantic，SQLAlchemy 2.x，LangChain（现有依赖但本特性不直接扩展其职责），React，Tailwind CSS，浏览器 Fetch API，Python 标准库 `hashlib`/`hmac`/`secrets`/`smtplib`

**Storage**: SQLite（复用 `server/.runtime` 下现有数据库文件并新增认证表），HTTP Only Cookie，文件日志

**Testing**: `pytest` 单元/契约/集成测试，`pnpm run typecheck`，`pnpm run build`，前端页面运行验证，后端日志与真实接口链路验证

**Target Platform**: 本地开发环境下的 Linux/macOS 后端进程与现代桌面浏览器

**Project Type**: 全栈 Web 应用认证子系统（FastAPI API + React feature）

**Performance Goals**: 验证码发送、注册、登录和刷新接口在本地开发环境中应于 2 秒内返回业务结果；验证码发送被限流时必须即时返回剩余等待信息；会话刷新链路在 access 会话到期后 10 秒内恢复可用访问

**Constraints**: 必须遵守后端 DDD + 整洁架构与前端 feature-based 结构；不得新增未批准第三方依赖；浏览器后续请求必须自动携带凭证；退出登录仅使当前浏览器当前会话失效；刷新资格必须一次性轮换；涉及 schema 变更必须提供幂等迁移脚本、验证步骤和失败恢复说明；所有认证失败必须显式记录日志并返回明确错误语义

**Scale/Scope**: 单仓库内新增 1 套认证域模型、1 组后端认证接口、1 个前端认证 feature、1 份 API 契约、1 套本地数据库迁移与验证说明；范围仅覆盖邮箱注册/登录/刷新/登出，不包含找回密码、第三方登录、多因子认证或全端强制登出

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`：虽然 [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) 仍是占位模板，当前治理以 [AGENTS.md](../../AGENTS.md) 为实际约束来源。
- `PASS`：后端方案限定为 FastAPI + SQLAlchemy + 标准库密码散列/SMTP 适配，遵守 `domain/application/infrastructure/presentation` 分层，不让应用层直接依赖基础设施实现。
- `PASS`：前端方案限定为 React + Tailwind CSS + feature-based 结构，仅新增 `ui/src/features/auth` 与共享 HTTP/组件接入，不绕过现有共享样式体系。
- `PASS`：未引入未批准第三方依赖；认证所需密码散列、会话标识与邮件发送能力均使用现有依赖和标准库完成。
- `PASS`：数据库变更已纳入设计范围，将通过显式迁移脚本、回滚说明、验证 SQL/测试和真实接口校验满足 AGENTS 的数据升级要求。
- `PASS`：验收路径覆盖自动化与真实链路验证，包含 pytest、前端类型检查/构建、浏览器手工验证、后端日志检查和 Cookie 会话验证。

### Post-Design Constitution Check

- `PASS`：设计产物已把认证能力限制在 `server/src/domain/auth`、`server/src/application/auth`、`server/src/infrastructure/*auth*`、`server/src/presentation/api/auth.py` 和 `ui/src/features/auth` 等局部目录中，未扩展到无关模块。
- `PASS`：设计明确使用当前浏览器 Cookie 会话、一次性刷新资格和 SMTP 适配器，避免引入 JWT 库、外部缓存或额外消息队列等未批准能力。
- `PASS`：设计包含迁移脚本、验证步骤、日志要求、契约测试和集成测试，符合“不得只凭代码改动判断完成”的要求。
- `PASS`：数据模型与契约已显式约束“退出仅影响当前会话”“刷新资格轮换”“验证码双重限流”和“密码最小强度”，减少后续实现歧义。

## Project Structure

### Documentation (this feature)

```text
specs/003-email-password-auth/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── auth-api.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
server/
├── pyproject.toml
├── .env.example
├── scripts/
│   └── migrate_auth_schema.py
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── domain/
│   │   └── auth/
│   │       ├── entities.py
│   │       ├── value_objects.py
│   │       └── services.py
│   ├── application/
│   │   └── auth/
│   │       ├── ports.py
│   │       ├── services.py
│   │       └── use_cases.py
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── auth_models.py
│   │   │   ├── auth_repository.py
│   │   │   └── auth_migrations.py
│   │   ├── security/
│   │   │   ├── password_hasher.py
│   │   │   └── cookie_session_manager.py
│   │   └── messaging/
│   │       └── smtp_email_sender.py
│   └── presentation/
│       └── api/
│           ├── auth.py
│           ├── health.py
│           └── dev_tasks.py
└── tests/
    ├── contract/
    │   └── test_auth_api.py
    ├── integration/
    │   └── test_auth_flow.py
    └── unit/
        └── auth/

ui/
├── package.json
├── .env.example
└── src/
    ├── app/
    │   └── App.tsx
    ├── features/
    │   ├── auth/
    │   │   ├── api.ts
    │   │   ├── components/
    │   │   ├── hooks/
    │   │   └── pages/
    │   ├── bootstrap-status/
    │   └── theme-showcase/
    └── shared/
        ├── components/
        ├── lib/
        │   └── http.ts
        └── styles/
```

**Structure Decision**: 采用现有双工程仓库结构。后端在 `server/src` 中新增独立 `auth` 垂直切片，领域规则和用例编排收敛到 `domain/auth` 与 `application/auth`，SMTP、密码散列、Cookie 会话与持久化实现位于 `infrastructure`；前端在 `ui/src/features/auth` 中新增认证页面、表单组件、状态 hook 与 API 封装，同时对共享 `http.ts` 做最小扩展以统一携带 Cookie。数据库迁移脚本独立放在 `server/scripts/`，避免把 schema 变更逻辑混入运行时应用层。

## Complexity Tracking

无宪章违规项，无需复杂度豁免。

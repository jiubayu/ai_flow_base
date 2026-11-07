# ui：Vite + React + Tailwind 前端

入口：`src/main.tsx` → `src/app/App.tsx`。

```bash
pnpm install
cp .env.example .env   # VITE_API_BASE_URL 必须与后端端口一致
pnpm dev               # http://127.0.0.1:5173（devctl 启动时会用 --port 传入 FRONTEND_PORT）
```

## 目录约定

```
src/
├── app/               # 应用壳：路由表（router.tsx）、路由守卫、导航
├── features/          # 按 feature 组织业务代码，每个 feature 自包含 api / hooks / components / pages
│   ├── auth/               # 认证：注册/登录表单、会话 hook（刷新与当前浏览器登出）、会话面板、AuthProvider
│   ├── workspace/          # 工作空间：切换与成员 API、useWorkspaceSession hook、切换器与成员面板
│   │                       # 005：应用 API、useWorkspace hook、卡片/表单/详情布局与列表页/详情页
│   └── bootstrap-status/   # 见 features/bootstrap-status/README.md
└── shared/            # 跨 feature 复用：组件（StatusCard、PageShell）、HTTP 客户端、全局样式
```

## 路由

每个页面一条路由，不再把认证、工作空间、详情、主题与运行状态渲染在同一屏（`src/app/router.tsx`，react-router-dom）。

| 路由 | 页面 | 守卫 |
|------|------|------|
| `/` | 按登录状态分流 | 已登录 → `/workspace`，未登录 → `/auth` |
| `/auth` | 注册 / 登录表单 | 已登录则跳转 `/workspace` |
| `/workspace` | 应用卡片列表 | 需登录 |
| `/workspace/applications/:applicationId` | 应用详情（左信息、右只读空画布） | 需登录 |
| `/session` | 会话面板 + 工作空间切换与成员 | 需登录 |
| `/theme` | 主题展示 | 公开 |
| `/bootstrap` | 运行状态 | 公开 |

守卫与页面共用 `AuthProvider`（`features/auth/providers/AuthProvider.tsx`）提供的同一份会话状态：会话恢复期间不请求受保护数据，未登录访问受保护路由直接回到 `/auth`。详情页由 URL 参数决定应用，刷新、浏览器后退和直接输入地址都落到同一应用。

认证请求统一通过 `credentials: "include"` 携带 HttpOnly Cookie（`shared/lib/http.ts`）；`VITE_API_BASE_URL` 必须与后端 `FRONTEND_ORIGIN` 匹配，否则浏览器不会附带会话 Cookie。页面初始化时 `useAuthSession` 会自动恢复当前浏览器会话，access 过期后可通过 refresh 资格恢复。

新增功能建 `src/features/<feature>/`，内部按 `api.ts`、`hooks/`、`components/` 分层；只有确实跨 feature 复用的内容才进 `shared/`。

前端验收以运行验证和日志验证为准（`server/logs/frontend.log`），不新增组件级测试。`pnpm run typecheck` 必须通过。

工作空间：登录会话类型（`AuthSessionPayload`）包含 `workspace` 上下文；会话页 `/session`（`features/auth/pages/SessionPage.tsx`）展示当前工作空间摘要、`WorkspaceSwitcher`（可访问工作空间列表与切换）和 `WorkspaceMembersPanel`（成员列表）。管理操作（添加成员、变更角色、移除）仅对 `manager` 角色渲染，普通成员只读；权限或 last-manager 保护错误通过 `HttpError` 的 `code` + `message` 展示。`useWorkspaceSession(enabled)` 仅在已登录时发起请求。

### 应用工作空间（005）验收步骤

1. `pnpm run typecheck` 与 `pnpm run build` 必须通过。
2. 后端先执行 `uv run python scripts/migrate_workspace_schema.py` 并启动服务，再 `pnpm dev` 打开首页（首页按登录状态分流到 `/auth` 或 `/workspace`）。
3. 未登录：只展示认证入口，不请求 `/api/workspace/current`，不展示任何工作空间或应用数据；直接访问 `/workspace` 或 `/workspace/applications/:id` 时回到 `/auth`。
4. 登录后默认落在 `/workspace`：显示默认工作空间名称与应用卡片列表；无工作空间时由后端懒创建，前端不提供手动创建工作空间的入口。
5. 应用列表为空时显示空状态与创建入口；创建成功后新卡片立即出现在列表里，无需刷新页面。
6. 表单校验：名称 1-80 个非空白字符、描述 0-500 字符，字段错误显示在对应字段旁；重复名称时显示"应用名称已存在，请换一个名称"（对应 409）。
7. 从卡片进入详情（地址为 `/workspace/applications/:id`，刷新或浏览器后退仍停在同一应用）：左侧应用信息（名称、描述、状态、更新时间）与右侧只读空画布及"开始编排"入口；窄屏纵向堆叠且信息在前。左侧提供编辑入口，页面上没有任何删除入口，画布不提供节点添加/移动/连接/保存/运行控件。
8. 卡片与详情读取同一份应用数据，编辑后两处显示保持一致；"返回应用列表"是真实链接，回到卡片视图。
9. 浏览器控制台无报错；`server/logs/backend.log`（debug 级）可见概览读取、应用创建/编辑、详情读取的数据流记录，且不含 Cookie 或敏感值。

## 主题系统

- 主题入口：`src/shared/styles/tokens.css`（语义 token 的唯一事实来源）+ `src/shared/styles/components.css`（共享样式原语），由 `src/shared/styles/index.css` 接入全局。
- 展示页：`pnpm dev` 后访问首页的 `Theme Showcase` 区（`src/features/theme-showcase/`），包含 token 分类、组件状态矩阵、工作台式布局与评审检查项。
- 扩展流程：新增 token 走 `tokens.css` → `tailwind.config.ts` 映射 → `theme-tokens.ts` 登记；新增组件优先复用 `src/shared/components/ui/` 与 `src/shared/components/theme/` 的共享原语。命名与禁止模式见 `src/shared/styles/theme-guidelines.md`。
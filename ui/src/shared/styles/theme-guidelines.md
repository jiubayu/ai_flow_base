# 主题扩展准则

主题 token（`tokens.css`）是颜色、圆角、阴影、边框与状态语义的唯一事实来源。新增页面或组件时必须消费语义 token，不得引入局部硬编码样式。

## Token 命名

- 必须语义命名：`content-primary`、`surface-panel`、`edge-focus`、`accent-positive`。
- 禁止与用途脱节的命名（如 `red-500`）或与页面耦合的命名（如 `page-a-bg`、`card2-shadow`）。
- 新增 token 必须归属已知分类：文本、背景、边框、强调、状态、视觉节奏（圆角 / 阴影 / 间距 / 字号）。确需新分类时，在 `theme-tokens.ts` 与展示页补充该分类的用途说明。

## 允许的扩展方式

1. 在 `tokens.css` 对应分类下新增 CSS 变量。
2. 在 `tailwind.config.ts` 的 theme 扩展中映射该变量。
3. 在 `theme-tokens.ts` 登记 token 的语义角色，供展示页与文档复用。
4. 共享样式原语（`components.css`）只消费 token，不定义具体色值。

## 禁止的模式

- 组件内直接写死色值、圆角或阴影作为主样式来源。
- 绕过状态矩阵：可交互组件必须覆盖 default / hover / focus / selected / disabled 的适用状态（见 `contracts/theme-style-contract.md`）。
- 同一页面内混用互相冲突的圆角、边框强度或阴影语言。
- 引入未批准的 UI 框架或样式方案；shadcn/ui 封装（`shared/components/ui/`）必须以项目 token 为唯一事实来源。

## 页面层级

页面骨架必须保持三层可感知层级：页面底层（`surface-page`）、内容承载层（`surface-panel`）、浮动交互层（`surface-overlay`）。典型工作台式布局（顶部导航、筛选栏、卡片网格、信息列表、空态）的样例见展示页 `WorkbenchPreview`。

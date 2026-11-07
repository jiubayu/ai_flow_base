# 数据模型：项目主题样式系统

## 1. ThemeToken

- 用途：表达单个全局主题语义项，是视觉系统的基础单元。
- 字段：
  - `name`: 语义名称，例如文本、背景、边框、强调、状态、圆角、阴影、间距、字号层级
  - `category`: `text | background | border | accent | state | radius | shadow | spacing | typography`
  - `semantic_role`: 对应的使用语义说明
  - `value`: 该 token 的实际视觉值
  - `aliases`: 可映射到的共享类名或组件语义名
- 约束：
  - `name` 在全局主题范围内唯一。
  - 必须优先按语义命名，不允许以页面名或业务功能名命名。
  - 任何基础组件样式都必须能追溯到至少一个 `ThemeToken`。

## 2. TokenGroup

- 用途：对同类主题 token 进行分组，便于查阅和维护。
- 字段：
  - `group_name`
  - `tokens`
  - `description`
  - `usage_scope`
- 约束：
  - 每组必须具备明确用途，不允许出现“杂项”分组。
  - `usage_scope` 必须说明该组是全局通用、交互专用还是展示专用。

## 3. ComponentStyleRecipe

- 用途：表达一个基础组件如何消费主题 token 形成最终样式。
- 字段：
  - `component_name`: `button | input | card | tag | nav_item | filter_item | empty_state`
  - `size_variants`
  - `state_variants`
  - `token_bindings`: 组件外观与主题 token 的映射
  - `layout_rules`: 圆角、边框、阴影、间距等布局规则
- 约束：
  - 每个基础组件都必须至少定义默认态与一种交互态。
  - `token_bindings` 不得为空。
  - 同类组件在不同页面不得重新定义核心外观语义。

## 4. InteractionState

- 用途：表达组件或可点击区域在交互过程中的视觉状态。
- 字段：
  - `state_name`: `default | hover | focus | active | selected | disabled`
  - `background_token`
  - `border_token`
  - `text_token`
  - `shadow_token`
  - `accessibility_note`
- 约束：
  - `disabled` 必须与 `selected`、`hover`、`focus` 有明显区分。
  - `focus` 必须可被键盘用户感知。
  - 任一状态变化不得仅依赖颜色变化而完全缺少层级或边框提示。

## 5. SurfaceHierarchy

- 用途：表达页面、面板、浮层、可点击项和强调区域之间的层级关系。
- 字段：
  - `surface_name`
  - `level`: `page | panel | overlay | interactive | accent`
  - `background_token`
  - `border_token`
  - `shadow_token`
  - `contrast_expectation`
- 约束：
  - 同一页面中至少要能区分页面底层、信息承载层和浮动交互层。
  - 层级关系必须支持浅背景场景下的清晰对比。

## 6. ThemeShowcaseSection

- 用途：表达主题验收展示页中的一个展示区块。
- 字段：
  - `section_name`
  - `purpose`
  - `displayed_tokens`
  - `displayed_components`
  - `acceptance_checks`
- 约束：
  - 展示页必须覆盖 token 展示和组件状态展示两个维度。
  - 每个区块至少对应一个明确的人工验收动作。

## 关系概览

- `TokenGroup` 聚合多个 `ThemeToken`。
- `ComponentStyleRecipe` 通过 `token_bindings` 依赖 `ThemeToken`。
- `InteractionState` 为 `ComponentStyleRecipe` 提供状态矩阵。
- `SurfaceHierarchy` 定义页面级层次语义，并被组件和展示页复用。
- `ThemeShowcaseSection` 汇总 `ThemeToken` 与 `ComponentStyleRecipe` 作为验收入口。

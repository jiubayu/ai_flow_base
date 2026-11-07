export type TokenCategory =
  | "text"
  | "background"
  | "border"
  | "accent"
  | "state"
  | "radius"
  | "shadow"
  | "spacing"
  | "typography";

export interface ThemeToken {
  name: string;
  category: TokenCategory;
  semantic_role: string;
  value: string;
  aliases: string[];
}

export interface TokenGroup {
  group_name: string;
  tokens: ThemeToken[];
  description: string;
  usage_scope: string;
}

export const TOKEN_GROUPS: TokenGroup[] = [
  {
    group_name: "文本",
    description: "文本层级语义：按信息重要度选择，而非按具体色值。",
    usage_scope: "全局通用",
    tokens: [
      { name: "content-primary", category: "text", semantic_role: "主文本", value: "var(--color-content-primary)", aliases: ["text-content-primary", "text-level-1/2"] },
      { name: "content-secondary", category: "text", semantic_role: "次级文本", value: "var(--color-content-secondary)", aliases: ["text-content-secondary", "text-level-3"] },
      { name: "content-muted", category: "text", semantic_role: "弱提示文本", value: "var(--color-content-muted)", aliases: ["text-content-muted", "text-level-4"] },
      { name: "content-inverse", category: "text", semantic_role: "反白文本", value: "var(--color-content-inverse)", aliases: ["text-content-inverse"] },
      { name: "content-accent", category: "text", semantic_role: "强调文本", value: "var(--color-content-accent)", aliases: ["text-content-accent", "text-accent"] },
    ],
  },
  {
    group_name: "背景",
    description: "页面层级语义：页面底层、信息承载层、浮动交互层。",
    usage_scope: "全局通用",
    tokens: [
      { name: "surface-page", category: "background", semantic_role: "页面背景", value: "var(--color-surface-page)", aliases: ["bg-surface-page", "surface-page"] },
      { name: "surface-panel", category: "background", semantic_role: "面板背景", value: "var(--color-surface-panel)", aliases: ["bg-surface-panel", "surface-panel"] },
      { name: "surface-overlay", category: "background", semantic_role: "浮层背景", value: "var(--color-surface-overlay)", aliases: ["bg-surface-overlay", "surface-overlay"] },
      { name: "surface-hover", category: "background", semantic_role: "悬停背景", value: "var(--color-surface-hover)", aliases: ["bg-surface-hover"] },
      { name: "surface-selected", category: "background", semantic_role: "选中背景", value: "var(--color-surface-selected)", aliases: ["bg-surface-selected"] },
      { name: "surface-disabled", category: "background", semantic_role: "禁用背景", value: "var(--color-surface-disabled)", aliases: ["bg-surface-disabled"] },
    ],
  },
  {
    group_name: "边框",
    description: "低噪声边框语言：基础、弱、强调与聚焦四种强度。",
    usage_scope: "全局通用",
    tokens: [
      { name: "edge-base", category: "border", semantic_role: "基础边框", value: "var(--color-edge-base)", aliases: ["border-edge-base"] },
      { name: "edge-weak", category: "border", semantic_role: "弱边框", value: "var(--color-edge-weak)", aliases: ["border-edge-weak"] },
      { name: "edge-accent", category: "border", semantic_role: "强调边框", value: "var(--color-edge-accent)", aliases: ["border-edge-accent"] },
      { name: "edge-focus", category: "border", semantic_role: "聚焦边框", value: "var(--color-edge-focus)", aliases: ["border-edge-focus"] },
    ],
  },
  {
    group_name: "强调与状态",
    description: "明确但不过饱和的强调色与状态色。",
    usage_scope: "全局通用",
    tokens: [
      { name: "accent-primary", category: "accent", semantic_role: "主强调", value: "var(--color-accent-primary)", aliases: ["bg-accent-primary", "text-accent-primary"] },
      { name: "accent-secondary", category: "accent", semantic_role: "辅助强调", value: "var(--color-accent-secondary)", aliases: ["bg-accent-secondary"] },
      { name: "accent-positive", category: "accent", semantic_role: "正向状态", value: "var(--color-accent-positive)", aliases: ["text-accent-positive", "badge-positive"] },
      { name: "accent-warning", category: "accent", semantic_role: "警示状态", value: "var(--color-accent-warning)", aliases: ["text-accent-warning", "badge-warning"] },
      { name: "accent-negative", category: "accent", semantic_role: "错误状态", value: "var(--color-accent-negative)", aliases: ["text-accent-negative", "badge-negative"] },
    ],
  },
  {
    group_name: "交互状态",
    description: "状态矩阵：每个可交互组件的适用状态与 token 绑定。",
    usage_scope: "交互专用",
    tokens: [
      { name: "state-default", category: "state", semantic_role: "默认态", value: "surface-panel + edge-base + content-primary", aliases: ["interaction-interactive"] },
      { name: "state-hover", category: "state", semantic_role: "悬停态", value: "surface-hover", aliases: ["interaction-interactive:hover"] },
      { name: "state-focus", category: "state", semantic_role: "聚焦态", value: "edge-focus + focus ring", aliases: ["field-focus", "interaction-focus-static"] },
      { name: "state-selected", category: "state", semantic_role: "选中态", value: "surface-selected + edge-accent", aliases: ["interaction-selected"] },
      { name: "state-disabled", category: "state", semantic_role: "禁用态", value: "surface-disabled + edge-weak + content-muted", aliases: ["interaction-disabled"] },
    ],
  },
  {
    group_name: "视觉节奏",
    description: "圆角、阴影、间距与字号层级构成一致的节奏语言。",
    usage_scope: "全局通用",
    tokens: [
      { name: "radius-sm/md/lg", category: "radius", semantic_role: "柔和圆角三档", value: "6 / 10 / 14px", aliases: ["rounded-sm", "rounded-md", "rounded-lg"] },
      { name: "shadow-sm/md/lg", category: "shadow", semantic_role: "阴影三档（低噪声）", value: "1px / 12px / 32px", aliases: ["shadow-sm", "shadow-md", "shadow-lg"] },
      { name: "space-1..8", category: "spacing", semantic_role: "间距节奏", value: "4/8/12/16/24/32px", aliases: ["p-t-2", "gap-t-3"] },
      { name: "font-size-caption..display", category: "typography", semantic_role: "字号层级", value: "12/14/15/16/20/24px", aliases: ["text-caption", "text-body", "text-heading", "text-display"] },
    ],
  },
];

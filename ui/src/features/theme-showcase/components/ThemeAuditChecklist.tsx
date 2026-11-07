import { ThemeShowcaseShell } from "./ThemeShowcaseShell";

const CHECKS = [
  "文本、背景、边框、强调、状态色均来自语义 token，而非硬编码色值",
  "新增 token 归属已知分类；新分类必须在主题说明中补充用途",
  "可交互组件覆盖 default / hover / focus / selected / disabled 的适用状态",
  "页面底层、承载层、浮层三层可感知，圆角与阴影语言一致",
  "基础组件（按钮 / 输入框 / 卡片 / 标签 / 导航项 / 筛选项 / 空态）来自统一视觉基线",
];

export function ThemeAuditChecklist() {
  return (
    <ThemeShowcaseShell title="评审检查项" subtitle="新页面接入主题前，对照以下检查项。">
      <ul className="space-y-t-2">
        {CHECKS.map((check) => (
          <li key={check} className="flex items-start gap-t-2 text-body-sm text-content-secondary">
            <span className="mt-t-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border border-edge-accent bg-tint-neutral text-caption text-accent-primary">
              ✓
            </span>
            {check}
          </li>
        ))}
      </ul>
    </ThemeShowcaseShell>
  );
}

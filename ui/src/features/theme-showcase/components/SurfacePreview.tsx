import { ThemeShowcaseShell } from "./ThemeShowcaseShell";

export function SurfacePreview() {
  return (
    <ThemeShowcaseShell
      title="页面层级"
      subtitle="页面底层 → 面板承载层 → 浮层交互层：三层必须可感知，且圆角与阴影语言一致。"
    >
      <div className="surface-page rounded-md p-t-4">
        <p className="text-level-4">页面底层（surface-page）</p>
        <div className="surface-panel mt-t-3 p-t-4">
          <p className="text-level-3">面板承载层（surface-panel）</p>
          <div className="surface-overlay mt-t-3 p-t-3">
            <p className="text-level-3">浮层交互层（surface-overlay）</p>
            <button className="interaction-interactive mt-t-2 px-t-3 py-t-2 text-body-sm text-content-primary">
              可点击项（悬停 / 聚焦可感知）
            </button>
          </div>
        </div>
      </div>
    </ThemeShowcaseShell>
  );
}

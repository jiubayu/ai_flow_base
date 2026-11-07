import { ComponentStateShowcase } from "../components/ComponentStateShowcase";
import { SurfacePreview } from "../components/SurfacePreview";
import { ThemeAuditChecklist } from "../components/ThemeAuditChecklist";
import { ThemeTokenGallery } from "../components/ThemeTokenGallery";
import { WorkbenchPreview } from "../components/WorkbenchPreview";

export function ThemeShowcasePage() {
  return (
    <div className="mx-auto max-w-3xl space-y-t-6 p-t-6">
      <header>
        <h1 className="text-display text-content-primary">Theme Showcase</h1>
        <p className="mt-t-1 text-level-3">
          AI-Flow 风格主题基线：token 分类、组件状态矩阵、工作台式布局与评审入口。
        </p>
      </header>
      <ThemeTokenGallery />
      <SurfacePreview />
      <ComponentStateShowcase />
      <WorkbenchPreview />
      <ThemeAuditChecklist />
    </div>
  );
}

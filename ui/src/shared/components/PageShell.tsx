import { type ReactNode } from "react";

// 跨 feature 复用的页面外壳：路由切换后各页面保持同一宽度与间距。
export function PageShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="mx-auto w-full max-w-3xl space-y-t-4 p-t-6">
      <header className="flex flex-col gap-t-1">
        <h1 className="text-level-1">{title}</h1>
        {subtitle ? <p className="text-caption text-content-muted">{subtitle}</p> : null}
      </header>
      {actions ? <div className="flex items-center justify-between gap-t-3">{actions}</div> : null}
      {children}
    </section>
  );
}

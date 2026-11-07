import { type ReactNode } from "react";

export interface ThemeShowcaseShellProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function ThemeShowcaseShell({ title, subtitle, children }: ThemeShowcaseShellProps) {
  return (
    <section className="surface-panel p-t-6">
      <header className="mb-t-4">
        <h2 className="text-level-2">{title}</h2>
        {subtitle ? <p className="mt-t-1 text-level-4">{subtitle}</p> : null}
      </header>
      {children}
    </section>
  );
}

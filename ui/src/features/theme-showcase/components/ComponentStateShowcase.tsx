import { type ReactNode } from "react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { EmptyState } from "@/shared/components/theme/EmptyState";
import { FilterChip } from "@/shared/components/theme/FilterChip";
import { NavItem } from "@/shared/components/theme/NavItem";
import { ThemeShowcaseShell } from "./ThemeShowcaseShell";

const STATES = ["default", "hover", "focus", "selected", "disabled"] as const;
type State = (typeof STATES)[number];

const stateClasses: Record<State, string> = {
  default: "",
  hover: "bg-surface-hover",
  focus: "ring-2 ring-edge-focus",
  selected: "bg-surface-selected border-edge-accent",
  disabled: "bg-surface-disabled text-content-muted",
};

const rows: { label: string; render: (state: State) => ReactNode }[] = [
  {
    label: "Button",
    render: (state) => (
      <Button variant="secondary" className={stateClasses[state]} disabled={state === "disabled"}>
        {state}
      </Button>
    ),
  },
  {
    label: "Input",
    render: (state) => (
      <Input
        className={stateClasses[state]}
        value="示例文本"
        readOnly
        disabled={state === "disabled"}
      />
    ),
  },
  {
    label: "Card",
    render: (state) => (
      <Card className={stateClasses[state]}>
        <span className="text-body-sm text-content-secondary">{state}</span>
      </Card>
    ),
  },
  {
    label: "NavItem",
    render: (state) => (
      <NavItem
        className={stateClasses[state]}
        active={state === "selected"}
        disabled={state === "disabled"}
      >
        {state}
      </NavItem>
    ),
  },
  {
    label: "FilterChip",
    render: (state) => (
      <FilterChip
        className={stateClasses[state]}
        active={state === "selected"}
        disabled={state === "disabled"}
      >
        {state}
      </FilterChip>
    ),
  },
  {
    label: "Badge",
    render: (state) =>
      state === "default" ? <Badge>default</Badge> : <span className="text-level-4">—</span>,
  },
];

export function ComponentStateShowcase() {
  return (
    <ThemeShowcaseShell
      title="基础组件状态矩阵"
      subtitle="每类组件的默认 / 悬停 / 聚焦 / 选中 / 禁用状态；悬停与聚焦以静态等价类呈现。"
    >
      <table className="w-full border-collapse text-left">
        <thead>
          <tr>
            <th className="pb-t-2 text-level-4">组件</th>
            {STATES.map((state) => (
              <th key={state} className="pb-t-2 text-level-4">
                {state}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <td className="py-t-2 text-body-sm font-medium text-content-primary">{row.label}</td>
              {STATES.map((state) => (
                <td key={state} className="py-t-2">
                  {row.render(state)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-t-4">
        <EmptyState title="空态容器" description="非交互容器：以面板层级 + 弱提示文本呈现，无状态矩阵。" />
      </div>
    </ThemeShowcaseShell>
  );
}

import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/shared/lib/utils";

export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action, className, ...props }: EmptyStateProps) {
  return (
    <div
      className={cn("surface-panel flex flex-col items-center gap-t-2 p-t-8 text-center", className)}
      {...props}
    >
      <p className="text-level-2">{title}</p>
      {description ? <p className="text-level-4">{description}</p> : null}
      {action ? <div className="mt-t-3">{action}</div> : null}
    </div>
  );
}

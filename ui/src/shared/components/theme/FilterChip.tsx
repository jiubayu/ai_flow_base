import { type ButtonHTMLAttributes } from "react";
import { cn } from "@/shared/lib/utils";

export interface FilterChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function FilterChip({ active, className, ...props }: FilterChipProps) {
  return (
    <button
      className={cn(
        "interaction-interactive rounded-full border border-edge-base px-t-3 py-t-1 text-caption font-medium text-content-secondary",
        active && "interaction-selected text-content-primary",
        className
      )}
      {...props}
    />
  );
}

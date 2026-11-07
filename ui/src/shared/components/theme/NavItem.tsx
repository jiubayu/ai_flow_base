import { type ButtonHTMLAttributes } from "react";
import { cn } from "@/shared/lib/utils";

export interface NavItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function NavItem({ active, className, ...props }: NavItemProps) {
  return (
    <button
      className={cn(
        "interaction-interactive px-t-3 py-t-2 text-body-sm text-content-secondary",
        active && "interaction-selected font-medium text-content-primary",
        className
      )}
      {...props}
    />
  );
}

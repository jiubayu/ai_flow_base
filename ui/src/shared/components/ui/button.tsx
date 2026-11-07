import { type ButtonHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/shared/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-t-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-edge-focus disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary:
          "bg-accent-primary text-content-inverse hover:bg-accent-secondary active:bg-accent-primary disabled:bg-surface-disabled disabled:text-content-muted",
        secondary:
          "border border-edge-base bg-surface-panel text-content-primary hover:bg-surface-hover active:bg-surface-selected disabled:bg-surface-disabled disabled:text-content-muted",
        ghost:
          "border border-transparent bg-transparent text-content-secondary hover:bg-surface-hover active:bg-surface-selected disabled:text-content-muted",
      },
      size: {
        sm: "rounded-sm px-t-2 py-t-1 text-caption",
        md: "rounded-md px-t-3 py-t-2 text-body-sm",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

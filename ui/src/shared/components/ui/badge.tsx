import { type HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/shared/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-t-2 py-t-1 text-caption font-medium",
  {
    variants: {
      variant: {
        neutral: "bg-tint-neutral text-content-secondary",
        positive: "bg-tint-positive text-accent-positive",
        warning: "bg-tint-warning text-accent-warning",
        negative: "bg-tint-negative text-accent-negative",
      },
    },
    defaultVariants: { variant: "neutral" },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

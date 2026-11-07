import { type ForwardedRef, type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/shared/lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "field-focus w-full rounded-md border border-edge-base bg-surface-panel px-t-3 py-t-2 text-body-sm text-content-primary placeholder:text-content-muted disabled:cursor-not-allowed disabled:bg-surface-disabled disabled:text-content-muted",
          className
        )}
        {...props}
      />
    );
  }
);

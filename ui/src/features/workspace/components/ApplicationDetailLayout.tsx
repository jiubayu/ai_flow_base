import { type ReactNode } from "react";

// 窄屏纵向堆叠时信息面板在前、画布在后；宽屏则左右分栏。
export function ApplicationDetailLayout({ info, canvas }: { info: ReactNode; canvas: ReactNode }) {
  return (
    <div className="flex flex-col gap-t-4 md:flex-row">
      <div className="md:w-80 md:shrink-0">{info}</div>
      <div className="md:flex-1">{canvas}</div>
    </div>
  );
}

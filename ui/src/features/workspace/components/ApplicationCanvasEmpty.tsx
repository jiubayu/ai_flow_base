import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import type { ApplicationCanvas } from "../api";

// 首版画布只读：这里只是编排入口，不提供节点添加、移动、连接、保存或运行能力。
export function ApplicationCanvasEmpty({ canvas }: { canvas: ApplicationCanvas }) {
  return (
    <Card className="flex min-h-[260px] flex-col gap-t-3">
      <CardHeader>
        <CardTitle>编排画布</CardTitle>
        <span className="text-caption text-content-muted">{canvas.editable ? "可编辑" : "只读"}</span>
      </CardHeader>
      <CardContent className="flex flex-col gap-t-2">
        <p className="text-body-sm text-content-secondary">画布当前为空，这是后续流程编排的入口。</p>
        <Button size="sm" disabled>
          {canvas.entry_label}
        </Button>
        <p className="text-caption text-content-muted">
          首版不支持节点的添加、移动、连接与保存，编辑能力将在后续版本开放。
        </p>
      </CardContent>
    </Card>
  );
}

import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { formatDateTime } from "@/shared/lib/format";
import type { ApplicationCard as ApplicationCardData } from "../api";
import { statusLabel } from "../lib/status";

// 首版没有删除能力，卡片只提供进入详情的入口。
export function ApplicationCard({
  application,
  onOpen,
}: {
  application: ApplicationCardData;
  onOpen: (applicationId: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{application.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-t-2">
        <p className="text-body-sm text-content-secondary">
          {application.description || `状态：${statusLabel(application.status)}`}
        </p>
        <p className="text-caption text-content-muted">更新于 {formatDateTime(application.updated_at)}</p>
        <Button size="sm" variant="secondary" onClick={() => onOpen(application.application_id)}>
          进入详情
        </Button>
      </CardContent>
    </Card>
  );
}

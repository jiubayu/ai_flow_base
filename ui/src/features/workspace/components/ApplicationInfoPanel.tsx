import { useState } from "react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { formatDateTime } from "@/shared/lib/format";
import type { ApplicationDetail } from "../api";
import { statusLabel } from "../lib/status";
import { ApplicationForm } from "./ApplicationForm";

export function ApplicationInfoPanel({
  application,
  error,
  onUpdate,
}: {
  application: ApplicationDetail;
  error: string | null;
  onUpdate: (name: string, description: string) => Promise<boolean>;
}) {
  const [editing, setEditing] = useState(false);

  if (editing) {
    return (
      <ApplicationForm
        mode="edit"
        initialName={application.name}
        initialDescription={application.description}
        error={error}
        onSubmit={async (name, description) => {
          const ok = await onUpdate(name, description);
          if (ok) {
            setEditing(false);
          }
          return ok;
        }}
        onCancel={() => setEditing(false)}
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{application.name}</CardTitle>
        <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
          编辑
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-t-2">
        <div className="flex flex-col gap-t-1">
          <span className="text-caption text-content-muted">描述</span>
          <p className="text-body-sm text-content-secondary">{application.description || "（无描述）"}</p>
        </div>
        <div className="flex items-center gap-t-2">
          <span className="text-caption text-content-muted">状态</span>
          <Badge variant="neutral">{statusLabel(application.status)}</Badge>
        </div>
        <div className="flex flex-col gap-t-1">
          <span className="text-caption text-content-muted">创建时间</span>
          <p className="text-caption text-content-secondary">{formatDateTime(application.created_at)}</p>
        </div>
        <div className="flex flex-col gap-t-1">
          <span className="text-caption text-content-muted">更新时间</span>
          <p className="text-caption text-content-secondary">{formatDateTime(application.updated_at)}</p>
        </div>
      </CardContent>
    </Card>
  );
}

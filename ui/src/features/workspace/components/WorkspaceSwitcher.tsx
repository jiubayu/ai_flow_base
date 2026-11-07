import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { EmptyState } from "@/shared/components/theme/EmptyState";
import type { WorkspaceController } from "../hooks/useWorkspaceSession";

export function WorkspaceSwitcher({ workspace }: { workspace: WorkspaceController }) {
  if (workspace.loading) {
    return (
      <div className="text-body-sm text-content-secondary" role="status">
        正在加载工作空间…
      </div>
    );
  }

  if (workspace.error) {
    return (
      <div className="text-caption text-content-accent" role="alert">
        {workspace.error}
      </div>
    );
  }

  if (workspace.available.length === 0) {
    return <EmptyState title="没有可访问的工作空间" description="注册后会自动创建你的默认工作空间。" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>工作空间</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-t-2" aria-label="可访问的工作空间列表">
          {workspace.available.map((ws) => (
            <li key={ws.workspace_id} className="flex items-center justify-between gap-t-2">
              <span className="flex items-center gap-t-2">
                {ws.name}
                <Badge variant={ws.role === "manager" ? "positive" : "neutral"}>
                  {ws.role === "manager" ? "管理者" : "成员"}
                </Badge>
              </span>
              {ws.is_current ? (
                <Badge variant="warning">当前</Badge>
              ) : (
                <Button size="sm" variant="secondary" onClick={() => workspace.switchTo(ws.workspace_id)}>
                  切换
                </Button>
              )}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

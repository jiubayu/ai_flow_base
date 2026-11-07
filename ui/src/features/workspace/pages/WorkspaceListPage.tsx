import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { PageShell } from "@/shared/components/PageShell";
import { Button } from "@/shared/components/ui/button";
import { useAuth } from "@/features/auth/providers/AuthProvider";
import { ApplicationForm } from "../components/ApplicationForm";
import { ApplicationGrid } from "../components/ApplicationGrid";
import { WorkspaceEmptyState } from "../components/WorkspaceEmptyState";
import { useWorkspace } from "../hooks/useWorkspace";

// 列表页只负责概览与卡片；详情由路由 /workspace/applications/:applicationId 承载。
export function WorkspaceListPage() {
  const auth = useAuth();
  const workspace = useWorkspace(auth.session !== null);
  const navigate = useNavigate();
  const nameInputRef = useRef<HTMLInputElement>(null);

  const handleCreate = async (name: string, description: string) => {
    const created = await workspace.createApplication(name, description);
    if (!created) {
      return false;
    }
    // 新卡片已经写入列表，随后进入它的详情页。
    navigate(`/workspace/applications/${created.application.application_id}`);
    return true;
  };

  if (workspace.loading) {
    return (
      <PageShell title="应用工作空间">
        <p className="text-body-sm text-content-secondary" role="status">
          正在加载你的工作空间…
        </p>
      </PageShell>
    );
  }

  return (
    <PageShell
      title={workspace.workspace?.name ?? "工作空间"}
      subtitle={workspace.workspace?.is_default ? "你的默认工作空间" : "当前工作空间"}
      actions={
        <Button size="sm" variant="secondary" onClick={() => void workspace.refresh()}>
          刷新
        </Button>
      }
    >
      <ApplicationForm mode="create" onSubmit={handleCreate} error={workspace.error} nameInputRef={nameInputRef} />

      {workspace.applications.length === 0 ? (
        <WorkspaceEmptyState onCreateEntry={() => nameInputRef.current?.focus()} />
      ) : (
        <ApplicationGrid
          applications={workspace.applications}
          onOpen={(applicationId) => navigate(`/workspace/applications/${applicationId}`)}
        />
      )}
    </PageShell>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageShell } from "@/shared/components/PageShell";
import { useAuth } from "@/features/auth/providers/AuthProvider";
import { type ApplicationDetailResponse } from "../api";
import { ApplicationCanvasEmpty } from "../components/ApplicationCanvasEmpty";
import { ApplicationDetailLayout } from "../components/ApplicationDetailLayout";
import { ApplicationInfoPanel } from "../components/ApplicationInfoPanel";
import { useWorkspace } from "../hooks/useWorkspace";

// 详情由 URL 上的 applicationId 决定：刷新、后退与直接输入地址都能回到同一应用。
export function ApplicationDetailPage() {
  const auth = useAuth();
  const { applicationId = "" } = useParams<{ applicationId: string }>();
  const { error, workspace, loadDetail, updateApplication } = useWorkspace(auth.session !== null);
  const [detail, setDetail] = useState<ApplicationDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);

  useEffect(() => {
    setDetailLoading(true);
    setDetail(null);
    void loadDetail(applicationId).then((loaded) => {
      setDetail(loaded);
      setDetailLoading(false);
    });
  }, [applicationId, loadDetail]);

  const handleUpdate = async (name: string, description: string) => {
    if (!detail) {
      return false;
    }
    const updated = await updateApplication(detail.application.application_id, name, description);
    if (!updated) {
      return false;
    }
    setDetail(updated);
    return true;
  };

  if (detailLoading) {
    return (
      <PageShell title="应用详情" subtitle={workspace?.name ?? "工作空间"}>
        <p className="text-body-sm text-content-secondary" role="status">
          正在加载应用详情…
        </p>
      </PageShell>
    );
  }

  if (!detail) {
    return (
      <PageShell
        title="应用详情"
        subtitle={workspace?.name ?? "工作空间"}
        actions={
          <Link className="text-body-sm text-content-accent" to="/workspace">
            返回应用列表
          </Link>
        }
      >
        <p className="text-caption text-content-accent" role="alert">
          {error ?? "应用不存在或无权访问"}
        </p>
      </PageShell>
    );
  }

  return (
    <PageShell
      title={detail.application.name}
      subtitle={workspace?.name ?? "工作空间"}
      actions={
        <Link className="text-body-sm text-content-accent" to="/workspace">
          返回应用列表
        </Link>
      }
    >
      <ApplicationDetailLayout
        info={<ApplicationInfoPanel application={detail.application} error={error} onUpdate={handleUpdate} />}
        canvas={<ApplicationCanvasEmpty canvas={detail.canvas} />}
      />
    </PageShell>
  );
}

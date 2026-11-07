import { PageShell } from "@/shared/components/PageShell";
import { WorkspaceMembersPanel } from "@/features/workspace/components/WorkspaceMembersPanel";
import { WorkspaceSwitcher } from "@/features/workspace/components/WorkspaceSwitcher";
import { useWorkspaceSession } from "@/features/workspace/hooks/useWorkspaceSession";
import { AuthSessionPanel } from "../components/AuthSessionPanel";
import { useAuth } from "../providers/AuthProvider";

// 会话与 004 的工作空间切换/成员管理独立成页，不再与认证表单混在同一屏。
export function SessionPage() {
  const auth = useAuth();
  const workspace = useWorkspaceSession(auth.session !== null);

  return (
    <PageShell title="会话与工作空间" subtitle="当前浏览器会话、可访问工作空间与成员">
      <div className="flex flex-col gap-t-4">
        <AuthSessionPanel auth={auth} />
        <WorkspaceSwitcher workspace={workspace} />
        <WorkspaceMembersPanel workspace={workspace} />
      </div>
    </PageShell>
  );
}

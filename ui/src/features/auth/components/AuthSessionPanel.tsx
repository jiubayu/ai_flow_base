import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import type { AuthController } from "../hooks/useAuthSession";

export function AuthSessionPanel({ auth }: { auth: AuthController }) {
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const session = auth.session;
  if (!session) return null;

  const handleRefresh = async () => {
    setBusy(true);
    setLocalError(null);
    try {
      await auth.refresh();
    } catch (err) {
      setLocalError(String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    setBusy(true);
    setLocalError(null);
    try {
      await auth.logoutAccount();
    } catch (err) {
      setLocalError(String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>当前登录状态</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-t-3">
        <p>用户：{session.user.email}</p>
        <p>
          当前工作空间：
          {session.workspace.current
            ? `${session.workspace.current.name}（${session.workspace.current.role === "manager" ? "管理者" : "成员"}）`
            : "无"}
        </p>
        <p>access 过期时间：{new Date(session.session.access_expires_at).toLocaleString()}</p>
        <p>refresh 过期时间：{new Date(session.session.refresh_expires_at).toLocaleString()}</p>
        {(auth.error ?? localError) && <p className="text-caption text-content-accent">{auth.error ?? localError}</p>}
        <div className="flex gap-t-2">
          <Button variant="secondary" onClick={handleRefresh} disabled={busy}>
            {busy ? "处理中…" : "刷新会话"}
          </Button>
          <Button onClick={handleLogout} disabled={busy}>
            退出登录
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

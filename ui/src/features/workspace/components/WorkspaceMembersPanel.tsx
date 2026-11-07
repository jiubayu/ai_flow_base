import { useEffect, useState } from "react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { EmptyState } from "@/shared/components/theme/EmptyState";
import { addMember, changeMemberRole, listMembers, removeMember, WorkspaceMember } from "../api";
import { toErrorText, type WorkspaceController } from "../hooks/useWorkspaceSession";

type MemberRole = WorkspaceMember["role"];

export function WorkspaceMembersPanel({ workspace }: { workspace: WorkspaceController }) {
  const isManager = workspace.current?.role === "manager";
  const currentWorkspaceId = workspace.current?.workspace_id ?? null;
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [newRole, setNewRole] = useState<MemberRole>("member");

  useEffect(() => {
    if (!currentWorkspaceId) {
      setMembers([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    listMembers()
      .then(({ members: list }) => setMembers(list))
      .catch((err) => setError(toErrorText(err)))
      .finally(() => setLoading(false));
  }, [currentWorkspaceId]);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(toErrorText(err));
    } finally {
      setBusy(false);
    }
  };

  const handleAdd = () => {
    const name = username.trim();
    if (!name) return;
    run(async () => {
      const { member } = await addMember(name, newRole);
      setMembers((prev) => [...prev, member]);
      setUsername("");
    });
  };

  const handleRoleChange = (userId: string, role: MemberRole) => {
    run(async () => {
      const { member } = await changeMemberRole(userId, role);
      setMembers((prev) => prev.map((m) => (m.user_id === userId ? member : m)));
    });
  };

  const handleRemove = (userId: string) => {
    run(async () => {
      await removeMember(userId);
      setMembers((prev) => prev.filter((m) => m.user_id !== userId));
    });
  };

  if (workspace.loading) {
    return (
      <div className="text-body-sm text-content-secondary" role="status">
        正在加载成员…
      </div>
    );
  }

  if (!workspace.current) {
    return <EmptyState title="没有当前工作空间" description="请先切换到一个可访问的工作空间。" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>成员</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-t-3">
        {loading ? (
          <div className="text-body-sm text-content-secondary" role="status">
            正在加载成员…
          </div>
        ) : members.length === 0 ? (
          <EmptyState title="没有成员" />
        ) : (
          <ul className="flex flex-col gap-t-2" aria-label="成员列表">
            {members.map((member) => (
              <li key={member.user_id} className="flex items-center justify-between gap-t-2">
                <span className="flex items-center gap-t-2">
                  {member.username}
                  <Badge variant={member.role === "manager" ? "positive" : "neutral"}>
                    {member.role === "manager" ? "管理者" : "成员"}
                  </Badge>
                </span>
                {isManager && (
                  <span className="flex items-center gap-t-2">
                    <select
                      aria-label={`变更 ${member.username} 的角色`}
                      value={member.role}
                      disabled={busy}
                      onChange={(e) => handleRoleChange(member.user_id, e.target.value as MemberRole)}
                    >
                      <option value="manager">manager</option>
                      <option value="member">member</option>
                    </select>
                    <Button size="sm" variant="ghost" disabled={busy} onClick={() => handleRemove(member.user_id)}>
                      移除
                    </Button>
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}

        {error && (
          <p className="text-caption text-content-accent" role="alert">
            {error}
          </p>
        )}

        {isManager && (
          <div className="flex items-center gap-t-2">
            <Input
              aria-label="要添加的用户名"
              placeholder="用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <select aria-label="新成员角色" value={newRole} onChange={(e) => setNewRole(e.target.value as MemberRole)}>
              <option value="member">member</option>
              <option value="manager">manager</option>
            </select>
            <Button size="sm" disabled={busy || !username.trim()} onClick={handleAdd}>
              添加成员
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

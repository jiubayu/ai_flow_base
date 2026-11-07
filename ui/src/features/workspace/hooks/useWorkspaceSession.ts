import { useCallback, useEffect, useState } from "react";
import { HttpError } from "@/shared/lib/http";
import { listWorkspaces, switchWorkspace, WorkspaceSummary } from "../api";

interface WorkspaceSessionState {
  current: WorkspaceSummary | null;
  available: WorkspaceSummary[];
  loading: boolean;
  error: string | null;
}

export function toErrorText(error: unknown): string {
  if (error instanceof HttpError) {
    return error.code ? `${error.code}：${error.message}` : error.message;
  }
  return String(error);
}

export function useWorkspaceSession(enabled: boolean) {
  const [state, setState] = useState<WorkspaceSessionState>({
    current: null,
    available: [],
    loading: enabled,
    error: null,
  });

  useEffect(() => {
    if (!enabled) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));
    listWorkspaces()
      .then(({ workspaces }) => {
        setState({
          current: workspaces.find((ws) => ws.is_current) ?? null,
          available: workspaces,
          loading: false,
          error: null,
        });
      })
      .catch((error) => setState((prev) => ({ ...prev, loading: false, error: toErrorText(error) })));
  }, [enabled]);

  const switchTo = useCallback(async (workspaceId: string) => {
    try {
      const context = await switchWorkspace(workspaceId);
      setState((prev) => ({ ...prev, current: context.current, available: context.available, error: null }));
      return context;
    } catch (error) {
      setState((prev) => ({ ...prev, error: toErrorText(error) }));
      return null;
    }
  }, []);

  return { ...state, switchTo };
}

export type WorkspaceController = ReturnType<typeof useWorkspaceSession>;

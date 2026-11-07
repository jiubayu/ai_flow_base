import { useCallback, useEffect, useState } from "react";
import { HttpError } from "@/shared/lib/http";
import {
  type ApplicationCard,
  type WorkspaceOverview,
  createWorkspaceApplication,
  getCurrentWorkspace,
  getWorkspaceApplication,
  updateWorkspaceApplication,
} from "../api";
import { toErrorText } from "./useWorkspaceSession";

// 服务端错误码到用户可读文案的映射：重复名称与字段校验必须给出明确提示。
const FRIENDLY_ERROR_MESSAGES: Record<string, string> = {
  APPLICATION_NAME_DUPLICATED: "应用名称已存在，请换一个名称",
  APPLICATION_NAME_INVALID: "应用名称必须为 1-80 个非空白字符",
  APPLICATION_DESCRIPTION_INVALID: "应用描述不能超过 500 字符",
  APPLICATION_NOT_FOUND: "应用不存在或无权访问",
  AUTH_SESSION_MISSING: "登录状态已失效，请重新登录",
  AUTH_SESSION_EXPIRED: "登录状态已失效，请重新登录",
};

export function toWorkspaceErrorText(error: unknown): string {
  if (error instanceof HttpError && error.code && FRIENDLY_ERROR_MESSAGES[error.code]) {
    return FRIENDLY_ERROR_MESSAGES[error.code];
  }
  return toErrorText(error);
}

interface WorkspaceState {
  workspace: WorkspaceOverview | null;
  applications: ApplicationCard[];
  loading: boolean;
  error: string | null;
}

export function useWorkspace(enabled: boolean) {
  const [state, setState] = useState<WorkspaceState>({
    workspace: null,
    applications: [],
    loading: enabled,
    error: null,
  });

  const refresh = useCallback(async () => {
    if (!enabled) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const overview = await getCurrentWorkspace();
      setState({
        workspace: overview.workspace,
        applications: overview.applications,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error: toWorkspaceErrorText(error) }));
    }
  }, [enabled]);

  useEffect(() => {
    if (enabled) void refresh();
  }, [enabled, refresh]);

  const createApplication = useCallback(async (name: string, description: string) => {
    try {
      const detail = await createWorkspaceApplication(name, description);
      // 创建后无需刷新即可看到新卡片。
      setState((prev) => ({ ...prev, applications: [detail.application, ...prev.applications], error: null }));
      return detail;
    } catch (error) {
      setState((prev) => ({ ...prev, error: toWorkspaceErrorText(error) }));
      return null;
    }
  }, []);

  const updateApplication = useCallback(async (applicationId: string, name: string, description: string) => {
    try {
      const detail = await updateWorkspaceApplication(applicationId, name, description);
      // 卡片与详情页共用同一份应用数据，编辑后两处显示保持一致。
      setState((prev) => ({
        ...prev,
        applications: prev.applications.map((app) =>
          app.application_id === detail.application.application_id ? detail.application : app
        ),
        error: null,
      }));
      return detail;
    } catch (error) {
      setState((prev) => ({ ...prev, error: toWorkspaceErrorText(error) }));
      return null;
    }
  }, []);

  const loadDetail = useCallback(async (applicationId: string) => {
    try {
      const detail = await getWorkspaceApplication(applicationId);
      setState((prev) => ({ ...prev, error: null }));
      return detail;
    } catch (error) {
      setState((prev) => ({ ...prev, error: toWorkspaceErrorText(error) }));
      return null;
    }
  }, []);

  return { ...state, refresh, createApplication, updateApplication, loadDetail };
}

// 与 004 的 WorkspaceController（工作空间切换）区分：这里管理的是应用与画布。
export type WorkspaceAppController = ReturnType<typeof useWorkspace>;

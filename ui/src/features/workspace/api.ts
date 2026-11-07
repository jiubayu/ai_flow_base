import { httpJson } from "@/shared/lib/http";

export interface WorkspaceSummary {
  workspace_id: string;
  name: string;
  role: "manager" | "member";
  is_current: boolean;
}

export interface WorkspaceMember {
  user_id: string;
  username: string;
  role: "manager" | "member";
  joined_at: string;
}

export interface WorkspaceContext {
  current: WorkspaceSummary | null;
  available: WorkspaceSummary[];
}

export function listWorkspaces(): Promise<{ workspaces: WorkspaceSummary[] }> {
  return httpJson<{ workspaces: WorkspaceSummary[] }>("/api/workspaces");
}

export function switchWorkspace(workspaceId: string): Promise<WorkspaceContext> {
  return httpJson<WorkspaceContext>("/api/workspaces/current", {
    method: "POST",
    body: JSON.stringify({ workspace_id: workspaceId }),
  });
}

export function listMembers(): Promise<{ members: WorkspaceMember[] }> {
  return httpJson<{ members: WorkspaceMember[] }>("/api/workspaces/current/members");
}

export function addMember(username: string, role: WorkspaceMember["role"]): Promise<{ member: WorkspaceMember }> {
  return httpJson<{ member: WorkspaceMember }>("/api/workspaces/current/members", {
    method: "POST",
    body: JSON.stringify({ username, role }),
  });
}

export function changeMemberRole(userId: string, role: WorkspaceMember["role"]): Promise<{ member: WorkspaceMember }> {
  return httpJson<{ member: WorkspaceMember }>(`/api/workspaces/current/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function removeMember(userId: string): Promise<void> {
  return httpJson<void>(`/api/workspaces/current/members/${userId}`, { method: "DELETE" });
}

// ----------------------------------------------------------------------
// 005：默认工作空间概览与应用（contracts/workspace-api.openapi.yaml）
// ----------------------------------------------------------------------

export interface WorkspaceOverview {
  workspace_id: string;
  name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCard {
  application_id: string;
  name: string;
  description: string;
  status: string;
  updated_at: string;
}

export interface ApplicationDetail extends ApplicationCard {
  created_at: string;
}

export interface ApplicationCanvas {
  mode: string;
  editable: boolean;
  entry_label: string;
}

export interface ApplicationDetailResponse {
  application: ApplicationDetail;
  canvas: ApplicationCanvas;
}

export interface WorkspaceOverviewResponse {
  workspace: WorkspaceOverview;
  applications: ApplicationCard[];
}

export function getCurrentWorkspace(): Promise<WorkspaceOverviewResponse> {
  return httpJson<WorkspaceOverviewResponse>("/api/workspace/current");
}

export function createWorkspaceApplication(
  name: string,
  description: string
): Promise<ApplicationDetailResponse> {
  return httpJson<ApplicationDetailResponse>("/api/workspace/applications", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export function updateWorkspaceApplication(
  applicationId: string,
  name: string,
  description: string
): Promise<ApplicationDetailResponse> {
  return httpJson<ApplicationDetailResponse>(`/api/workspace/applications/${applicationId}`, {
    method: "PATCH",
    body: JSON.stringify({ name, description }),
  });
}

export function getWorkspaceApplication(applicationId: string): Promise<ApplicationDetailResponse> {
  return httpJson<ApplicationDetailResponse>(`/api/workspace/applications/${applicationId}`);
}

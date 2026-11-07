import { httpJson } from "@/shared/lib/http";
import type { WorkspaceContext } from "@/features/workspace/api";

export interface AuthUser {
  user_id: string;
  email: string;
  email_verified: boolean;
}

export interface AuthSessionInfo {
  authenticated: boolean;
  access_expires_at: string;
  refresh_expires_at: string;
}

export interface AuthSessionPayload {
  user: AuthUser;
  session: AuthSessionInfo;
  workspace: WorkspaceContext;
}

export interface CodeAccepted {
  status: string;
  retry_after_seconds: number;
  expires_in_seconds: number;
}

export function sendEmailCode(email: string): Promise<CodeAccepted> {
  return httpJson<CodeAccepted>("/api/auth/email-code", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function register(email: string, code: string, password: string): Promise<AuthSessionPayload> {
  return httpJson<AuthSessionPayload>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, code, password }),
  });
}

export function login(email: string, password: string): Promise<AuthSessionPayload> {
  return httpJson<AuthSessionPayload>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getSession(): Promise<AuthSessionPayload> {
  return httpJson<AuthSessionPayload>("/api/auth/session");
}

export function refreshSession(): Promise<AuthSessionPayload> {
  return httpJson<AuthSessionPayload>("/api/auth/refresh", { method: "POST" });
}

export function logout(): Promise<void> {
  return httpJson<void>("/api/auth/logout", { method: "POST" });
}

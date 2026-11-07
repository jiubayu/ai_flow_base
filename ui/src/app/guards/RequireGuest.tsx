import { type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/features/auth/providers/AuthProvider";
import { RestoringSession } from "../components/RestoringSession";

// 已登录用户不再停留在认证页：登录/注册成功后直接落到工作空间。
export function RequireGuest({ children }: { children: ReactNode }) {
  const auth = useAuth();

  if (auth.restoring) {
    return <RestoringSession />;
  }
  if (auth.session) {
    return <Navigate to="/workspace" replace />;
  }
  return <>{children}</>;
}

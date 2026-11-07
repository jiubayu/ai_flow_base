import { type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/features/auth/providers/AuthProvider";
import { RestoringSession } from "../components/RestoringSession";

// 未登录时不请求受保护数据，直接回到认证页。
export function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuth();

  if (auth.restoring) {
    return <RestoringSession />;
  }
  if (!auth.session) {
    return <Navigate to="/auth" replace />;
  }
  return <>{children}</>;
}

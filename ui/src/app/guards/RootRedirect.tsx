import { Navigate } from "react-router-dom";
import { useAuth } from "@/features/auth/providers/AuthProvider";
import { RestoringSession } from "../components/RestoringSession";

// 首页与未知路径按登录状态分流：登录后落在工作空间，未登录落在认证页。
export function RootRedirect() {
  const auth = useAuth();

  if (auth.restoring) {
    return <RestoringSession />;
  }
  return <Navigate to={auth.session ? "/workspace" : "/auth"} replace />;
}

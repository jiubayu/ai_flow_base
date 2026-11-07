import { createContext, useContext, type ReactNode } from "react";
import { type AuthController, useAuthSession } from "../hooks/useAuthSession";

const AuthContext = createContext<AuthController | null>(null);

// 会话在路由之间共享：守卫与各页面读取同一个 Provider，避免每个页面各自恢复会话。
export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuthSession();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthController {
  const auth = useContext(AuthContext);
  if (auth === null) {
    throw new Error("useAuth 必须在 AuthProvider 内使用");
  }
  return auth;
}

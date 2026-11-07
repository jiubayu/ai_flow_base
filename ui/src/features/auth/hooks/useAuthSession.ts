import { useCallback, useEffect, useState } from "react";
import { HttpError } from "@/shared/lib/http";
import {
  AuthSessionPayload,
  CodeAccepted,
  getSession,
  login,
  logout,
  refreshSession,
  register,
  sendEmailCode,
} from "../api";

interface AuthSessionState {
  session: AuthSessionPayload | null;
  restoring: boolean;
  error: string | null;
}

export function useAuthSession() {
  const [state, setState] = useState<AuthSessionState>({ session: null, restoring: true, error: null });

  useEffect(() => {
    getSession()
      .then((session) => setState({ session, restoring: false, error: null }))
      .catch(async (error) => {
        if (error instanceof HttpError && error.status === 401) {
          try {
            const recovered = await refreshSession();
            setState({ session: recovered, restoring: false, error: null });
            return;
          } catch (refreshError) {
            if (refreshError instanceof HttpError && refreshError.status === 401) {
              setState({ session: null, restoring: false, error: null });
              return;
            }
            setState({ session: null, restoring: false, error: String(refreshError) });
            return;
          }
        }
        setState({ session: null, restoring: false, error: String(error) });
      });
  }, []);

  const sendCode = useCallback(async (email: string): Promise<CodeAccepted> => {
    return sendEmailCode(email);
  }, []);

  const registerAccount = useCallback(async (email: string, code: string, password: string) => {
    const payload = await register(email, code, password);
    setState({ session: payload, restoring: false, error: null });
    return payload;
  }, []);

  const loginAccount = useCallback(async (email: string, password: string) => {
    const payload = await login(email, password);
    setState({ session: payload, restoring: false, error: null });
    return payload;
  }, []);

  const refresh = useCallback(async () => {
    try {
      const payload = await refreshSession();
      setState({ session: payload, restoring: false, error: null });
      return payload;
    } catch (error) {
      if (error instanceof HttpError && error.status === 401) {
        setState({ session: null, restoring: false, error: "刷新资格已失效，请重新登录" });
      } else {
        setState((prev) => ({ ...prev, error: String(error) }));
      }
      return null;
    }
  }, []);

  const logoutAccount = useCallback(async () => {
    await logout();
    setState({ session: null, restoring: false, error: null });
  }, []);

  return {
    session: state.session,
    restoring: state.restoring,
    error: state.error,
    sendCode,
    registerAccount,
    loginAccount,
    refresh,
    logoutAccount,
  };
}

export type AuthController = ReturnType<typeof useAuthSession>;

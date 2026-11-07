import { Route, Routes } from "react-router-dom";
import { AuthPage } from "@/features/auth/pages/AuthPage";
import { SessionPage } from "@/features/auth/pages/SessionPage";
import { BootstrapStatusPanel } from "@/features/bootstrap-status/components/BootstrapStatusPanel";
import { ThemeShowcasePage } from "@/features/theme-showcase/pages/ThemeShowcasePage";
import { ApplicationDetailPage } from "@/features/workspace/pages/ApplicationDetailPage";
import { WorkspaceListPage } from "@/features/workspace/pages/WorkspaceListPage";
import { NotFoundPage } from "./components/NotFoundPage";
import { RequireAuth } from "./guards/RequireAuth";
import { RequireGuest } from "./guards/RequireGuest";
import { RootRedirect } from "./guards/RootRedirect";

// 每个页面一条路由：不再把认证、工作空间、详情、主题与运行状态渲染在同一屏。
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />

      <Route
        path="/auth"
        element={
          <RequireGuest>
            <AuthPage />
          </RequireGuest>
        }
      />

      <Route
        path="/workspace"
        element={
          <RequireAuth>
            <WorkspaceListPage />
          </RequireAuth>
        }
      />

      <Route
        path="/workspace/applications/:applicationId"
        element={
          <RequireAuth>
            <ApplicationDetailPage />
          </RequireAuth>
        }
      />

      <Route
        path="/session"
        element={
          <RequireAuth>
            <SessionPage />
          </RequireAuth>
        }
      />

      <Route path="/theme" element={<ThemeShowcasePage />} />
      <Route path="/bootstrap" element={<BootstrapStatusPanel />} />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

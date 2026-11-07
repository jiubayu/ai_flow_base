import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/features/auth/providers/AuthProvider";
import { AppNav } from "./components/AppNav";
import { AppRoutes } from "./router";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="surface-page min-h-screen font-theme">
          <AppNav />
          <AppRoutes />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

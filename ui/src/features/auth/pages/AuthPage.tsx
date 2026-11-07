import { PageShell } from "@/shared/components/PageShell";
import { useAuth } from "../providers/AuthProvider";
import { LoginForm } from "../components/LoginForm";
import { RegisterForm } from "../components/RegisterForm";

// 认证页只负责注册与登录；登录成功后由路由守卫落到工作空间。
export function AuthPage() {
  const auth = useAuth();

  return (
    <PageShell title="登录 / 注册" subtitle="登录或注册后进入你的默认工作空间">
      {auth.error ? (
        <p className="text-caption text-content-accent" role="alert">
          {auth.error}
        </p>
      ) : null}
      <div className="flex flex-col gap-t-4">
        <RegisterForm auth={auth} />
        <LoginForm auth={auth} />
      </div>
    </PageShell>
  );
}

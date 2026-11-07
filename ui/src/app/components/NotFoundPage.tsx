import { Link } from "react-router-dom";
import { PageShell } from "@/shared/components/PageShell";

export function NotFoundPage() {
  return (
    <PageShell title="页面不存在" subtitle="该地址没有对应路由">
      <p className="text-body-sm text-content-secondary" role="alert">
        请返回 <Link className="text-content-accent" to="/">首页</Link> 或从导航选择页面。
      </p>
    </PageShell>
  );
}

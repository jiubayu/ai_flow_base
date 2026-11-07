import { NavLink } from "react-router-dom";
import { cn } from "@/shared/lib/utils";

const LINKS = [
  { to: "/workspace", label: "应用工作空间" },
  { to: "/session", label: "会话与工作空间" },
  { to: "/theme", label: "主题展示" },
  { to: "/bootstrap", label: "运行状态" },
];

// 路由入口：与共享 NavItem 保持同一视觉语义，但用真实链接以便浏览器可直达与后退。
export function AppNav() {
  return (
    <nav className="flex flex-wrap gap-t-1 border-b border-edge-base px-t-6 py-t-2" aria-label="页面导航">
      {LINKS.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          className={({ isActive }) =>
            cn(
              "interaction-interactive px-t-3 py-t-2 text-body-sm text-content-secondary",
              isActive && "interaction-selected font-medium text-content-primary"
            )
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}

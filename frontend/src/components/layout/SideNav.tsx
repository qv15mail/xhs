import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Radar,
  FileText,
  BarChart3,
  PenLine,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { to: "/", label: "仪表盘", icon: LayoutDashboard, end: true },
  { to: "/collect", label: "采集", icon: Radar },
  { to: "/notes", label: "笔记库", icon: FileText },
  { to: "/insights", label: "分析", icon: BarChart3 },
  { to: "/compose", label: "仿写", icon: PenLine },
  { to: "/settings", label: "设置", icon: Settings },
];

export function SideNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex h-full w-60 flex-col border-r border-border bg-surface">
      <div className="flex h-16 items-center gap-2 border-b border-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-fg">
          <Radar className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight text-text">RedScope</p>
          <p className="text-xs text-text-mut">采集 · 分析 · 仿写</p>
        </div>
      </div>
      <div className="flex-1 space-y-1 p-3">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-bg text-text"
                  : "text-text-mut hover:bg-bg hover:text-text",
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-primary" />
                )}
                <Icon className="h-[18px] w-[18px]" />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </div>
      <div className="border-t border-border p-3 text-xs leading-relaxed text-text-mut">
        仅供个人创作研究，请遵守平台规则。
      </div>
    </nav>
  );
}

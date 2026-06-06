import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Menu, Plus, ScanLine } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { LoginDialog } from "@/components/layout/LoginDialog";
import { api } from "@/api/client";
import { useAppStore } from "@/store/app";
import { cn } from "@/lib/utils";

export function TopBar({ onMenu }: { onMenu: () => void }) {
  const navigate = useNavigate();
  const loggedIn = useAppStore((s) => s.loggedIn);
  const setLoggedIn = useAppStore((s) => s.setLoggedIn);
  const [loginOpen, setLoginOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await api.logout();
      setLoggedIn(false);
    } finally {
      setLoggingOut(false);
    }
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenu}
          aria-label="打开导航"
          className="rounded-md p-2 text-text-mut hover:bg-bg md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="hidden sm:block">
          <p className="text-sm font-medium text-text">小红书内容工作台</p>
          <p className="text-xs text-text-mut">主题驱动的采集分析与仿写</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => !loggedIn && setLoginOpen(true)}
          className={cn(
            "flex items-center gap-2 rounded-md border border-border px-3 py-1.5 transition-colors",
            !loggedIn && "hover:bg-bg",
          )}
          aria-label={loggedIn ? "登录态在线" : "点击扫码登录"}
        >
          <span
            className={cn("h-2 w-2 rounded-full", loggedIn ? "bg-success" : "bg-text-mut/50")}
          />
          <span className="text-xs text-text-mut">{loggedIn ? "登录态在线" : "未登录"}</span>
        </button>

        {loggedIn ? (
          <Button size="sm" variant="secondary" loading={loggingOut} onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            退出登录
          </Button>
        ) : (
          <Button size="sm" variant="secondary" onClick={() => setLoginOpen(true)}>
            <ScanLine className="h-4 w-4" />
            扫码登录
          </Button>
        )}

        <Button size="sm" onClick={() => navigate("/collect")}>
          <Plus className="h-4 w-4" />
          新建采集
        </Button>
      </div>

      <LoginDialog open={loginOpen} onClose={() => setLoginOpen(false)} />
    </header>
  );
}

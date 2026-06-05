import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { Collect } from "@/pages/Collect";
import { Notes } from "@/pages/Notes";
import { Insights } from "@/pages/Insights";
import { Compose } from "@/pages/Compose";
import { Settings } from "@/pages/Settings";
import { api } from "@/api/client";
import { useAppStore } from "@/store/app";

export default function App() {
  const setLoggedIn = useAppStore((s) => s.setLoggedIn);

  useEffect(() => {
    let cancelled = false;
    api
      .authStatus()
      .then((s) => {
        if (!cancelled) setLoggedIn(Boolean(s?.loggedIn));
      })
      .catch(() => {
        /* 后端未启动或网络异常时保持默认状态 */
      });
    return () => {
      cancelled = true;
    };
  }, [setLoggedIn]);

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/collect" element={<Collect />} />
        <Route path="/notes" element={<Notes />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/compose" element={<Compose />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </AppShell>
  );
}

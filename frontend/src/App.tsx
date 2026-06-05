import { Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { Collect } from "@/pages/Collect";
import { Notes } from "@/pages/Notes";
import { Insights } from "@/pages/Insights";
import { Compose } from "@/pages/Compose";
import { Settings } from "@/pages/Settings";

export default function App() {
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

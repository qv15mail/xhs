import { useState, type ReactNode } from "react";
import { SideNav } from "./SideNav";
import { TopBar } from "./TopBar";
import { DisclaimerDialog } from "@/components/common/DisclaimerDialog";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileNav, setMobileNav] = useState(false);

  return (
    <div className="flex h-full">
      <DisclaimerDialog />

      <aside className="hidden md:block">
        <SideNav />
      </aside>

      {mobileNav && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setMobileNav(false)}
            aria-hidden
          />
          <div className="relative h-full">
            <SideNav onNavigate={() => setMobileNav(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setMobileNav(true)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="mx-auto max-w-[1440px]">{children}</div>
        </main>
      </div>
    </div>
  );
}

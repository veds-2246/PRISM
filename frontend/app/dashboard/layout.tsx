import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-surface md:block">
        <Sidebar />
      </aside>

      <div className="md:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center border-b border-border bg-surface/95 px-6 backdrop-blur">
          <div>
            <p className="text-sm font-medium text-foreground">
              Indian Standards Recommendation Engine
            </p>
            <p className="text-xs text-text-muted">
              Procurement decision support
            </p>
          </div>
          <div className="ml-auto text-xs text-text-muted"><span className="hidden sm:inline">Authenticated decision-support workspace</span></div>
        </header>

        <main className="min-h-[calc(100vh-4rem)] p-6">{children}</main>
      </div>
    </div>
  );
}

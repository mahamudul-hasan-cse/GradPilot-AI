"use client";

import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { ErrorBoundary } from "@/components/shared/error-boundary";

type AppShellProps = {
  children: React.ReactNode;
  title: string;
  description?: string;
};

export function AppShell({ children, title, description }: AppShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <AppHeader title={title} description={description} />
        <main className="flex-1 overflow-y-auto p-6" id="main-content">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

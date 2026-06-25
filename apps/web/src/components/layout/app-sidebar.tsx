"use client";

import {
  Bell,
  Bot,
  ChevronLeft,
  FileText,
  FolderOpen,
  GitBranch,
  GraduationCap,
  LayoutDashboard,
  Settings,
  Sparkles,
  User,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/app-store";

const ICONS = {
  LayoutDashboard,
  User,
  GraduationCap,
  Wallet,
  Bot,
  FolderOpen,
  FileText,
  GitBranch,
  Bell,
  Settings,
} as const;

export function AppSidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, unreadNotifications } = useAppStore();

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300",
        sidebarCollapsed ? "w-[68px]" : "w-64",
      )}
      aria-label="Main navigation"
    >
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Sparkles className="h-4 w-4" aria-hidden />
        </div>
        {!sidebarCollapsed && (
          <span className="font-semibold tracking-tight">GradPilot</span>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn("ml-auto h-7 w-7", sidebarCollapsed && "ml-0")}
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", sidebarCollapsed && "rotate-180")} />
        </Button>
      </div>

      <ScrollArea className="flex-1 px-2 py-4">
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = ICONS[item.icon as keyof typeof ICONS];
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-foreground",
                )}
                aria-current={active ? "page" : undefined}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden />
                {!sidebarCollapsed && (
                  <>
                    <span className="flex-1">{item.label}</span>
                    {item.href === "/notifications" && unreadNotifications > 0 && (
                      <Badge variant="default" className="h-5 min-w-5 px-1 text-[10px]">
                        {unreadNotifications}
                      </Badge>
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
    </aside>
  );
}

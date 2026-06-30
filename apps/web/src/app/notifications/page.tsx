"use client";

import { useEffect } from "react";
import { Bell, CheckCircle, FileText, GraduationCap, Sparkles } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTimeline } from "@/hooks/use-queries";
import { useAppStore } from "@/stores/app-store";

const ICON_MAP: Record<string, typeof Bell> = {
  document: FileText,
  documents: FileText,
  application: GraduationCap,
  applications: GraduationCap,
  profile: Sparkles,
  default: Bell,
};

export default function NotificationsPage() {
  const { data } = useTimeline();
  const { setUnreadNotifications } = useAppStore();
  const entries = data?.entries ?? [];

  useEffect(() => {
    setUnreadNotifications(0);
  }, [setUnreadNotifications]);

  return (
    <AppShell title="Notifications" description="Activity and updates from your journey">
      {entries.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="All caught up"
          description="You'll see notifications here when documents are processed, deadlines approach, or AI insights are ready."
        />
      ) : (
        <div className="space-y-3 max-w-2xl" role="list" aria-label="Notifications">
          {entries.map((entry) => {
            const eventKey = (entry.category ?? entry.event_type ?? "").split(".")[0];
            const Icon = ICON_MAP[eventKey] ?? ICON_MAP.default;
            return (
              <Card key={entry.id} role="listitem">
                <CardHeader className="flex flex-row items-start gap-4 pb-2">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Icon className="h-4 w-4" aria-hidden />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <CardTitle className="text-sm">{entry.title}</CardTitle>
                      <Badge variant="outline" className="text-[10px] shrink-0">
                        {new Date(entry.occurred_at).toLocaleDateString()}
                      </Badge>
                    </div>
                    {entry.description && (
                      <CardDescription className="mt-1">{entry.description}</CardDescription>
                    )}
                  </div>
                  <CheckCircle className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden />
                </CardHeader>
              </Card>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}

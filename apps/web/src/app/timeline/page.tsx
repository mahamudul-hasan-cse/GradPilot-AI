"use client";

import { useMemo } from "react";
import {
  BookOpen,
  Bot,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  FileText,
  GraduationCap,
  ListTodo,
  Milestone,
  RefreshCw,
} from "lucide-react";
import { useSession } from "next-auth/react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useTimeline } from "@/hooks/use-queries";
import { cn } from "@/lib/utils";
import type { TimelineEntry } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

type EventIcon = React.ElementType;

function iconForEvent(entry: TimelineEntry): EventIcon {
  const t = (entry.event_type ?? entry.category ?? "").toLowerCase();
  if (t.includes("document") || t.includes("upload")) return FileText;
  if (t.includes("application") || t.includes("apply")) return BriefcaseBusiness;
  if (t.includes("ai") || t.includes("chat") || t.includes("advisor")) return Bot;
  if (t.includes("plan") || t.includes("planner") || t.includes("task")) return ListTodo;
  if (t.includes("profile")) return GraduationCap;
  if (t.includes("scholarship")) return BookOpen;
  if (t.includes("university")) return GraduationCap;
  if (t.includes("complete") || t.includes("done")) return CheckCircle2;
  return Milestone;
}

function colorForEvent(entry: TimelineEntry): string {
  const t = (entry.event_type ?? entry.category ?? "").toLowerCase();
  if (t.includes("document") || t.includes("upload")) return "bg-blue-500";
  if (t.includes("application") || t.includes("apply")) return "bg-purple-500";
  if (t.includes("ai") || t.includes("chat")) return "bg-indigo-500";
  if (t.includes("plan")) return "bg-emerald-500";
  if (t.includes("profile")) return "bg-orange-500";
  if (t.includes("scholarship")) return "bg-yellow-500";
  if (t.includes("complete")) return "bg-green-500";
  return "bg-primary";
}

function groupByMonth(entries: TimelineEntry[]): Map<string, TimelineEntry[]> {
  const map = new Map<string, TimelineEntry[]>();
  for (const entry of entries) {
    const d = new Date(entry.occurred_at);
    const key = d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(entry);
  }
  return map;
}

export default function TimelinePage() {
  const { data: session } = useSession();
  const { data, isLoading } = useTimeline();
  const queryClient = useQueryClient();

  const entries = useMemo(
    () => [...(data?.entries ?? [])].sort(
      (a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime(),
    ),
    [data?.entries],
  );

  const grouped = useMemo(() => groupByMonth(entries), [entries]);

  function handleRefresh() {
    if (!session?.accessToken) return;
    api.student.refresh(session.accessToken).then(() => {
      queryClient.invalidateQueries({ queryKey: ["timeline"] });
    });
  }

  return (
    <AppShell
      title="Journey Timeline"
      description="Your complete study abroad journey, event by event"
    >
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {entries.length} event{entries.length !== 1 ? "s" : ""} recorded
        </p>
        <Button variant="outline" size="sm" onClick={handleRefresh} className="gap-1.5">
          <RefreshCw className="h-4 w-4" />
          Sync Events
        </Button>
      </div>

      {isLoading ? (
        <ListSkeleton count={5} />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="No timeline events yet"
          description="Events appear as you upload documents, create applications, chat with AI, and update your profile."
        />
      ) : (
        <div className="space-y-10">
          {Array.from(grouped.entries()).map(([month, monthEntries]) => (
            <div key={month}>
              {/* Month header */}
              <div className="mb-4 flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <CalendarDays className="h-4 w-4 text-muted-foreground" />
                  <h3 className="text-sm font-semibold">{month}</h3>
                  <Badge variant="secondary" className="text-xs">{monthEntries.length}</Badge>
                </div>
                <div className="h-px flex-1 bg-border" />
              </div>

              {/* Events */}
              <div className="relative space-y-0 ml-4">
                {/* Vertical line */}
                <div className="absolute left-3 top-4 bottom-4 w-px bg-border" />

                {monthEntries.map((entry, i) => {
                  const Icon = iconForEvent(entry);
                  const color = colorForEvent(entry);
                  const time = new Date(entry.occurred_at);
                  return (
                    <div key={entry.id} className="relative flex gap-4 pb-6 last:pb-0">
                      {/* Icon dot */}
                      <div className={cn(
                        "relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-white shadow-sm",
                        color,
                      )}>
                        <Icon className="h-3.5 w-3.5" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0 pb-1 pt-0.5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-sm font-medium leading-snug">{entry.title}</p>
                            {entry.description && (
                              <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{entry.description}</p>
                            )}
                          </div>
                          <time
                            dateTime={entry.occurred_at}
                            className="shrink-0 text-xs text-muted-foreground"
                          >
                            {time.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                            {" "}
                            {time.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true })}
                          </time>
                        </div>
                        {/* Category badge */}
                        {(entry.event_type ?? entry.category) && (
                          <div className="mt-1.5">
                            <Badge variant="outline" className="text-xs capitalize">
                              {entry.event_type ?? entry.category}
                            </Badge>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}

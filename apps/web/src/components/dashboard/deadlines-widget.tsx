"use client";

import { Calendar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useApplications } from "@/hooks/use-queries";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function isWithin30Days(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  const in30 = new Date();
  in30.setDate(now.getDate() + 30);
  return d > now && d <= in30;
}

export function DeadlinesWidget() {
  const { data, isLoading } = useApplications();
  const upcoming = (data ?? []).filter((a) => a.deadline && isWithin30Days(a.deadline)).slice(0, 4);

  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Upcoming Deadlines</CardTitle>
        <Calendar className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : upcoming.length === 0 ? (
          <p className="text-sm text-muted-foreground">No deadlines in the next 30 days.</p>
        ) : (
          <ul className="space-y-2" role="list">
            {upcoming.map((a) => (
              <li key={a.id} className="flex items-center justify-between text-sm">
                <span className="truncate">{a.notes ?? "Application"}</span>
                <Badge variant="outline">{a.deadline ? formatDate(a.deadline) : "—"}</Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

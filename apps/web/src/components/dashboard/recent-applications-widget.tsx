"use client";

import Link from "next/link";
import { ArrowRight, BriefcaseBusiness } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useApplications } from "@/hooks/use-queries";

const STATUS_PROGRESS: Record<string, number> = {
  planning: 15,
  preparing: 45,
  ready: 70,
  submitted: 80,
  interview: 90,
  accepted: 100,
  rejected: 100,
  deferred: 85,
  withdrawn: 100,
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function labelForStatus(status: string) {
  return status.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function RecentApplicationsWidget() {
  const { data, isLoading } = useApplications();
  const recent = [...(data ?? [])]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 3);

  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Recent Applications</CardTitle>
        <BriefcaseBusiness className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : recent.length === 0 ? (
          <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
            No applications yet. Start with one university you are serious about.
          </div>
        ) : (
          <div className="space-y-4">
            {recent.map((application) => {
              const progress = STATUS_PROGRESS[application.status] ?? 20;
              return (
                <Link
                  key={application.id}
                  href={`/applications/${application.id}`}
                  className="block rounded-xl border bg-background/50 p-3 transition-colors hover:bg-muted/50"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{application.notes || "Application workspace"}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Updated {formatDate(application.updated_at)}
                      </p>
                    </div>
                    <Badge variant={application.status === "accepted" ? "success" : "outline"}>
                      {labelForStatus(application.status)}
                    </Badge>
                  </div>
                  <Progress value={progress} className="mt-3" aria-label={`${progress}% application progress`} />
                </Link>
              );
            })}
          </div>
        )}

        <Button asChild variant="ghost" size="sm" className="mt-4 px-0">
          <Link href="/applications">
            View all applications <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

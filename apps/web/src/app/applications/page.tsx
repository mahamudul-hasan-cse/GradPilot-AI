"use client";

import Link from "next/link";
import { FolderOpen, Plus } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useApplications } from "@/hooks/use-queries";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline" | "success" | "warning"> = {
  planning: "outline",
  in_progress: "warning",
  submitted: "default",
  accepted: "success",
  rejected: "secondary",
};

export default function ApplicationsPage() {
  const { data, isLoading } = useApplications();

  return (
    <AppShell title="Application Workspace" description="Track and manage your applications">
      <div className="mb-6 flex justify-end">
        <Button asChild>
          <Link href="/applications/new">
            <Plus className="h-4 w-4" aria-hidden />
            New application
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <ListSkeleton />
      ) : !data?.length ? (
        <EmptyState
          icon={FolderOpen}
          title="No applications yet"
          description="Create your first application workspace to track tasks, documents, and deadlines."
          action={{ label: "Create application", href: "/applications/new" }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.map((app) => (
            <Link key={app.id} href={`/applications/${app.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{app.notes ?? "Application"}</CardTitle>
                    <Badge variant={STATUS_VARIANT[app.status] ?? "outline"}>
                      {app.status.replace("_", " ")}
                    </Badge>
                  </div>
                  <CardDescription>
                    {app.deadline ? `Deadline: ${new Date(app.deadline).toLocaleDateString()}` : "No deadline set"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Progress value={app.status === "submitted" ? 100 : app.status === "in_progress" ? 60 : 20} />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}

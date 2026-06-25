"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { CheckCircle2, Circle, FileText } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: session } = useSession();

  const { data, isLoading } = useQuery({
    queryKey: ["workspace", id],
    queryFn: () => api.applications.workspace(session!.accessToken, id),
    enabled: !!session?.accessToken && !!id,
  });

  if (isLoading) {
    return (
      <AppShell title="Application" description="Loading workspace...">
        <ListSkeleton count={3} />
      </AppShell>
    );
  }

  const workspace = data;
  const app = workspace?.application;

  return (
    <AppShell
      title={app?.notes ?? "Application Workspace"}
      description={`Status: ${app?.status?.replace("_", " ") ?? "unknown"}`}
    >
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm text-muted-foreground">{workspace?.progress_percent ?? 0}%</span>
        </div>
        <Progress value={workspace?.progress_percent ?? 0} aria-label="Application progress" />
      </div>

      <Tabs defaultValue="tasks">
        <TabsList>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="deadlines">Deadlines</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="mt-4 space-y-2">
          {(workspace?.tasks ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No tasks yet. Generate tasks from templates.</p>
          ) : (
            workspace?.tasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="flex items-center gap-3 p-4">
                  {task.status === "completed" ? (
                    <CheckCircle2 className="h-4 w-4 text-success" aria-hidden />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground" aria-hidden />
                  )}
                  <span className={cn("flex-1 text-sm", task.status === "completed" && "line-through text-muted-foreground")}>
                    {task.title}
                  </span>
                  <Badge variant="outline">{task.status}</Badge>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="documents" className="mt-4 space-y-2">
          {(workspace?.documents ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents attached.</p>
          ) : (
            workspace?.documents.map((doc) => (
              <Card key={doc.id}>
                <CardHeader className="flex flex-row items-center gap-3 p-4">
                  <FileText className="h-4 w-4 text-muted-foreground" aria-hidden />
                  <div className="flex-1">
                    <CardTitle className="text-sm">{doc.title}</CardTitle>
                    <p className="text-xs text-muted-foreground">{doc.document_type}</p>
                  </div>
                  <Badge variant="secondary">{doc.status}</Badge>
                </CardHeader>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="deadlines" className="mt-4 space-y-2">
          {(workspace?.deadlines ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No deadlines set.</p>
          ) : (
            workspace?.deadlines.map((d) => (
              <Card key={d.id}>
                <CardContent className="flex items-center justify-between p-4">
                  <span className="text-sm font-medium">{d.title}</span>
                  <Badge variant={d.is_completed ? "success" : "warning"}>
                    {new Date(d.due_date).toLocaleDateString()}
                  </Badge>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}

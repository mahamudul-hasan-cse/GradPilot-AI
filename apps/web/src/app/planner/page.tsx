"use client";

import { useQuery } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import {
  AlertTriangle,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  ChevronRight,
  Clock,
  RefreshCw,
  Target,
  TrendingUp,
  User,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api, type PlannerTask } from "@/lib/api";
import { useProfile, useProfileAnalysis } from "@/hooks/use-queries";
import { cn } from "@/lib/utils";

const PRIORITY_COLORS: Record<string, string> = {
  high: "destructive",
  critical: "destructive",
  medium: "warning",
  low: "secondary",
};

function priorityColor(score: number): string {
  if (score >= 80) return "destructive";
  if (score >= 60) return "warning";
  return "secondary";
}

function TaskItem({ task }: { task: PlannerTask }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border p-3 hover:bg-muted/30 transition-colors">
      <div className={cn("mt-0.5 h-2 w-2 shrink-0 rounded-full", task.status === "completed" ? "bg-green-500" : "bg-primary")} />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium leading-snug">{task.title}</p>
          <Badge variant={priorityColor(task.priority_score) as any} className="shrink-0 text-xs">
            {Math.round(task.priority_score)}
          </Badge>
        </div>
        {task.reason && <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{task.reason}</p>}
        <div className="mt-1.5 flex items-center gap-2">
          <Badge variant="outline" className="text-xs capitalize">{task.category}</Badge>
          {task.due_date && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {new Date(task.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PlannerPage() {
  const { data: session } = useSession();
  const { data: profile } = useProfile();
  const { data: analysis } = useProfileAnalysis();

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["planner-plan", session?.user?.id],
    queryFn: () => api.planner.plan(session!.accessToken),
    enabled: !!session?.accessToken,
    retry: false,
  });

  const hasProfile = !!(profile?.gpa && profile?.field_of_study);

  return (
    <AppShell
      title="Study Abroad Planner"
      description="AI-generated action plan based on your profile"
    >
      {/* Profile snapshot strip */}
      {hasProfile && (
        <div className="mb-6 flex flex-wrap gap-3 rounded-xl border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-sm">
            <User className="h-4 w-4 text-primary" />
            <span className="font-medium">{profile?.field_of_study}</span>
          </div>
          {profile?.gpa && (
            <Badge variant="secondary" className="text-xs">GPA {profile.gpa}/{profile.gpa_scale ?? 4}</Badge>
          )}
          {(profile?.test_scores as any)?.ielts && (
            <Badge variant="secondary" className="text-xs">IELTS {(profile.test_scores as any).ielts}</Badge>
          )}
          {profile?.target_degree && (
            <Badge variant="outline" className="text-xs capitalize">{profile.target_degree}</Badge>
          )}
          {profile?.target_countries?.[0] && (
            <Badge variant="outline" className="text-xs">{profile.target_countries[0]}</Badge>
          )}
          {analysis && (
            <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
              <TrendingUp className="h-3.5 w-3.5 text-primary" />
              Readiness: <span className="font-semibold text-foreground">{Math.round(analysis.admission_readiness_score)}%</span>
            </div>
          )}
        </div>
      )}

      {isLoading ? (
        <ListSkeleton count={4} />
      ) : isError || !hasProfile ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <AlertTriangle className="h-8 w-8 text-muted-foreground" />
            <div>
              <p className="font-medium">Complete your profile first</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Add your GPA, IELTS score, and field of study to generate a personalized plan.
              </p>
            </div>
            <Button asChild variant="outline" size="sm">
              <a href="/profile">Go to Profile</a>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Stats row */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Card className="glass">
              <CardContent className="flex items-center gap-3 p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Target className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{Math.round(data?.priority_score ?? 0)}</p>
                  <p className="text-xs text-muted-foreground">Priority score</p>
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="flex items-center gap-3 p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-500/10 text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{data?.todays_tasks.length ?? 0}</p>
                  <p className="text-xs text-muted-foreground">Tasks today</p>
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="flex items-center gap-3 p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/10 text-orange-600">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {(data?.risk_alerts?.length ?? 0) + (data?.deadline_alerts?.length ?? 0)}
                  </p>
                  <p className="text-xs text-muted-foreground">Alerts</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Readiness progress */}
          {analysis && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  Readiness Scores
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-3">
                {[
                  { label: "Admission Readiness", value: analysis.admission_readiness_score },
                  { label: "Scholarship Readiness", value: analysis.scholarship_readiness_score },
                  { label: "Employability", value: analysis.employability_score },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="mb-1.5 flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{item.label}</span>
                      <span className="font-semibold">{Math.round(item.value)}%</span>
                    </div>
                    <Progress value={item.value} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Today's & Tomorrow's tasks */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <CalendarCheck className="h-4 w-4 text-primary" />
                  Today's Tasks
                  <Badge variant="secondary" className="text-xs">{data?.todays_tasks.length ?? 0}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(data?.todays_tasks.length ?? 0) === 0 ? (
                  <p className="text-sm text-muted-foreground">No tasks for today.</p>
                ) : (
                  <div className="space-y-2">
                    {data!.todays_tasks.map((t) => <TaskItem key={t.id} task={t} />)}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  Tomorrow's Tasks
                  <Badge variant="secondary" className="text-xs">{data?.tomorrows_tasks.length ?? 0}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(data?.tomorrows_tasks.length ?? 0) === 0 ? (
                  <p className="text-sm text-muted-foreground">No tasks scheduled for tomorrow.</p>
                ) : (
                  <div className="space-y-2">
                    {data!.tomorrows_tasks.map((t) => <TaskItem key={t.id} task={t} />)}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Weekly Goals */}
          {(data as any)?.weekly_goals?.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BookOpen className="h-4 w-4 text-primary" />
                  Weekly Goals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(data as any).weekly_goals.slice(0, 5).map((g: any, i: number) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                        {i + 1}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{g.title}</p>
                        {g.description && <p className="text-xs text-muted-foreground mt-0.5">{g.description}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Risk & Deadline Alerts */}
          {((data as any)?.risk_alerts?.length > 0 || (data as any)?.deadline_alerts?.length > 0) && (
            <Card className="border-orange-200 dark:border-orange-800">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm text-orange-600">
                  <AlertTriangle className="h-4 w-4" />
                  Alerts & Risks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[...((data as any).risk_alerts ?? []), ...((data as any).deadline_alerts ?? [])].slice(0, 6).map((a: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 rounded-lg bg-orange-50 dark:bg-orange-950/20 p-3">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-orange-500" />
                      <div>
                        <p className="text-xs font-medium">{a.title}</p>
                        {a.reason && <p className="mt-0.5 text-xs text-muted-foreground">{a.reason}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Missing Requirements */}
          {(data as any)?.missing_requirements?.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  Missing Requirements
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(data as any).missing_requirements.slice(0, 5).map((r: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground" />
                      <span>{r.title}: <span className="text-muted-foreground">{r.description}</span></span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Regenerate */}
          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching} className="gap-1.5">
              <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
              Regenerate Plan
            </Button>
          </div>
        </div>
      )}
    </AppShell>
  );
}

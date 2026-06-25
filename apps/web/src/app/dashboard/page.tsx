"use client";

import { useSession } from "next-auth/react";

import { AIInsightsWidget } from "@/components/dashboard/ai-insights-widget";
import { DeadlinesWidget } from "@/components/dashboard/deadlines-widget";
import { ProgressOverviewWidget } from "@/components/dashboard/progress-widget";
import { ReadinessWidget } from "@/components/dashboard/readiness-widget";
import { ScholarshipMatchesWidget } from "@/components/dashboard/scholarship-matches-widget";
import { ApplicationStatsWidget } from "@/components/dashboard/stats-widget";
import { TasksWidget } from "@/components/dashboard/tasks-widget";
import { UniversityMatchesWidget } from "@/components/dashboard/university-matches-widget";
import { AppShell } from "@/components/layout/app-shell";

export default function DashboardPage() {
  const { data: session } = useSession();

  return (
    <AppShell
      title={`Welcome back${session?.user?.name ? `, ${session.user.name.split(" ")[0]}` : ""}`}
      description="Your admission command center"
    >
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <ReadinessWidget />
        <AIInsightsWidget />
        <DeadlinesWidget />
        <TasksWidget />
        <UniversityMatchesWidget />
        <ScholarshipMatchesWidget />
        <ProgressOverviewWidget />
        <ApplicationStatsWidget />
      </div>
    </AppShell>
  );
}

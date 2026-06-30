"use client";

import { useSession } from "next-auth/react";

import { AIQuickActionsWidget } from "@/components/dashboard/ai-quick-actions-widget";
import { AIInsightsWidget } from "@/components/dashboard/ai-insights-widget";
import { DashboardSection } from "@/components/dashboard/dashboard-section";
import { DeadlinesWidget } from "@/components/dashboard/deadlines-widget";
import { ProfileProgressWidget } from "@/components/dashboard/profile-progress-widget";
import { ProgressOverviewWidget } from "@/components/dashboard/progress-widget";
import { ReadinessWidget } from "@/components/dashboard/readiness-widget";
import { RecentApplicationsWidget } from "@/components/dashboard/recent-applications-widget";
import { RecentDocumentsWidget } from "@/components/dashboard/recent-documents-widget";
import { ScholarshipMatchesWidget } from "@/components/dashboard/scholarship-matches-widget";
import { ApplicationStatsWidget } from "@/components/dashboard/stats-widget";
import { TasksWidget } from "@/components/dashboard/tasks-widget";
import { UniversityMatchesWidget } from "@/components/dashboard/university-matches-widget";
import { AppShell } from "@/components/layout/app-shell";
import { usePlannerTasksToday } from "@/hooks/use-queries";

export default function DashboardPage() {
  const { data: session } = useSession();
  const { data: plannerTasks } = usePlannerTasksToday();
  const tasks = plannerTasks?.map((task) => ({
    id: task.id,
    title: task.title,
    done: task.status === "completed",
  }));

  return (
    <AppShell
      title={`Welcome back${session?.user?.name ? `, ${session.user.name.split(" ")[0]}` : ""}`}
      description="Your admission command center"
    >
      <div className="space-y-8">
        <DashboardSection
          title="At a Glance"
          description="The few signals that matter most for your study abroad plan."
        >
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            <ReadinessWidget />
            <ProfileProgressWidget />
            <ApplicationStatsWidget />
            <ProgressOverviewWidget />
          </div>
        </DashboardSection>

        <DashboardSection title="Today" description="Focus on what moves your applications forward.">
          <div className="grid gap-6 lg:grid-cols-2">
            <TasksWidget tasks={tasks} />
            <DeadlinesWidget />
          </div>
        </DashboardSection>

        <DashboardSection title="Matches" description="Review the best-fit schools and funding options.">
          <div className="grid gap-6 lg:grid-cols-2">
            <UniversityMatchesWidget />
            <ScholarshipMatchesWidget />
          </div>
        </DashboardSection>

        <DashboardSection title="Recent Activity" description="Your latest applications and uploaded documents.">
          <div className="grid gap-6 lg:grid-cols-2">
            <RecentApplicationsWidget />
            <RecentDocumentsWidget />
          </div>
        </DashboardSection>

        <DashboardSection title="AI Guidance" description="Use AI for strategy, profile gaps, and next steps.">
          <div className="grid gap-6 lg:grid-cols-2">
            <AIInsightsWidget />
            <AIQuickActionsWidget />
          </div>
        </DashboardSection>
      </div>
    </AppShell>
  );
}

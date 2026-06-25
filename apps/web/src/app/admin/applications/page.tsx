"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getApiV1Url } from "@/lib/utils";

type Analytics = {
  total_applications: number;
  status_distribution: Record<string, number>;
  acceptance_rate: number;
  completion_rate: number;
  country_distribution: Record<string, number>;
  upcoming_deadlines: number;
  recent_applications: Array<{
    id: string;
    status: string;
    progress_percent: number;
    title: string | null;
    created_at: string;
  }>;
};

function MetricCard({ title, value, subtitle }: { title: string; value: string; subtitle?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
      {subtitle && (
        <CardContent>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </CardContent>
      )}
    </Card>
  );
}

export default function ApplicationsDashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${getApiV1Url()}/applications/analytics`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setAnalytics(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, [fetchAnalytics]);

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Application Workspace</h1>
          <p className="text-muted-foreground">Monitor applications, acceptance rates, and completion</p>
        </div>

        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6 text-destructive">{error}</CardContent>
          </Card>
        )}

        {loading && !analytics ? (
          <p className="text-muted-foreground">Loading analytics…</p>
        ) : analytics ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard title="Total Applications" value={String(analytics.total_applications)} />
              <MetricCard title="Acceptance Rate" value={`${analytics.acceptance_rate}%`} />
              <MetricCard title="Avg Completion" value={`${analytics.completion_rate}%`} />
              <MetricCard title="Upcoming Deadlines" value={String(analytics.upcoming_deadlines)} />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Status Distribution</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(analytics.status_distribution).map(([status, count]) => (
                    <div key={status} className="flex justify-between text-sm">
                      <span className="capitalize">{status}</span>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Country Distribution</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(analytics.country_distribution).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No data yet</p>
                  ) : (
                    Object.entries(analytics.country_distribution).map(([country, count]) => (
                      <div key={country} className="flex justify-between text-sm">
                        <span>{country}</span>
                        <Badge variant="outline">{count}</Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Applications</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="pb-2 pr-4">Title</th>
                      <th className="pb-2 pr-4">Status</th>
                      <th className="pb-2 pr-4">Progress</th>
                      <th className="pb-2">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.recent_applications.map((app) => (
                      <tr key={app.id} className="border-b">
                        <td className="py-2 pr-4">{app.title || "Untitled"}</td>
                        <td className="py-2 pr-4 capitalize">{app.status}</td>
                        <td className="py-2 pr-4">{app.progress_percent}%</td>
                        <td className="py-2 font-mono text-xs">
                          {new Date(app.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}

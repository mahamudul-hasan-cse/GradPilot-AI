"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getApiV1Url } from "@/lib/utils";

type Dashboard = {
  total_sources: number;
  active_sources: number;
  total_universities: number;
  avg_quality_score: number;
  failed_sources: number;
  recent_jobs: Array<{
    id: string;
    job_type: string;
    status: string;
    processed: number;
    succeeded: number;
    failed: number;
    duplicates_merged: number;
    embeddings_indexed: number;
    started_at: string | null;
    completed_at: string | null;
  }>;
};

export default function IngestionDashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${getApiV1Url()}/ingestion/dashboard`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDashboard(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  async function triggerJob(jobType: "incremental" | "full") {
    setTriggering(true);
    try {
      await fetch(`${getApiV1Url()}/ingestion/jobs/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_type: jobType }),
      });
      await fetchDashboard();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to trigger job");
    } finally {
      setTriggering(false);
    }
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Ingestion Monitor</h1>
            <p className="text-muted-foreground">University data pipeline health & job history</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={fetchDashboard} disabled={loading}>
              Refresh
            </Button>
            <Button onClick={() => triggerJob("incremental")} disabled={triggering}>
              Run Incremental
            </Button>
            <Button variant="secondary" onClick={() => triggerJob("full")} disabled={triggering}>
              Run Full
            </Button>
          </div>
        </div>

        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
          </Card>
        )}

        {loading && !dashboard ? (
          <p className="text-muted-foreground">Loading metrics…</p>
        ) : dashboard ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <MetricCard title="Sources" value={dashboard.total_sources} subtitle={`${dashboard.active_sources} active`} />
              <MetricCard title="Universities" value={dashboard.total_universities} subtitle="in PostgreSQL" />
              <MetricCard title="Avg Quality" value={`${dashboard.avg_quality_score}%`} subtitle="data quality score" />
              <MetricCard title="Failed Sources" value={dashboard.failed_sources} subtitle="3+ consecutive failures" />
              <MetricCard title="Recent Jobs" value={dashboard.recent_jobs.length} subtitle="last 10 runs" />
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Jobs</CardTitle>
                <CardDescription>Scrape → Extract → Normalize → Validate → Dedup → Load → Embed</CardDescription>
              </CardHeader>
              <CardContent>
                {dashboard.recent_jobs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No jobs yet. Load sources and trigger a job.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-muted-foreground">
                          <th className="pb-2 pr-4">Type</th>
                          <th className="pb-2 pr-4">Status</th>
                          <th className="pb-2 pr-4">Processed</th>
                          <th className="pb-2 pr-4">Succeeded</th>
                          <th className="pb-2 pr-4">Failed</th>
                          <th className="pb-2 pr-4">Deduped</th>
                          <th className="pb-2 pr-4">Embedded</th>
                          <th className="pb-2">Completed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dashboard.recent_jobs.map((job) => (
                          <tr key={job.id} className="border-b last:border-0">
                            <td className="py-3 pr-4 font-medium">{job.job_type}</td>
                            <td className="py-3 pr-4">
                              <StatusBadge status={job.status} />
                            </td>
                            <td className="py-3 pr-4">{job.processed}</td>
                            <td className="py-3 pr-4 text-green-600">{job.succeeded}</td>
                            <td className="py-3 pr-4 text-destructive">{job.failed}</td>
                            <td className="py-3 pr-4">{job.duplicates_merged}</td>
                            <td className="py-3 pr-4">{job.embeddings_indexed}</td>
                            <td className="py-3 text-muted-foreground">
                              {job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle }: { title: string; value: string | number; subtitle: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant = status.includes("completed") ? "default" : status === "running" ? "secondary" : "outline";
  return <Badge variant={variant}>{status}</Badge>;
}

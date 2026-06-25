"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getApiV1Url } from "@/lib/utils";

type Analytics = {
  total_analyses: number;
  avg_admission_readiness_score: number;
  avg_scholarship_readiness_score: number;
  avg_employability_score: number;
  cache_hit_rate: number;
  tier_distribution: Record<string, number>;
  analyzer_distribution: Record<string, number>;
  recent_analyses: Array<{
    id: string;
    admission_score: number;
    scholarship_score: number;
    employability_score: number;
    tier: string | null;
    analyzer_type: string;
    cache_hit: boolean;
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

export default function ProfileIntelligenceDashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${getApiV1Url()}/profile/analyze/analytics`, { cache: "no-store" });
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
          <h1 className="text-3xl font-bold">Profile Intelligence</h1>
          <p className="text-muted-foreground">
            Student profile analysis metrics, tier distribution, and recent runs
          </p>
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
              <MetricCard title="Total Analyses" value={String(analytics.total_analyses)} />
              <MetricCard
                title="Avg Admission Readiness"
                value={`${analytics.avg_admission_readiness_score}`}
                subtitle="0–100 scale"
              />
              <MetricCard
                title="Avg Scholarship Readiness"
                value={`${analytics.avg_scholarship_readiness_score}`}
              />
              <MetricCard
                title="Cache Hit Rate"
                value={`${analytics.cache_hit_rate}%`}
                subtitle={`Employability avg: ${analytics.avg_employability_score}`}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>University Tier Distribution</CardTitle>
                  <CardDescription>Recommended tiers across all analyses</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(analytics.tier_distribution).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No data yet</p>
                  ) : (
                    Object.entries(analytics.tier_distribution).map(([tier, count]) => (
                      <div key={tier} className="flex items-center justify-between text-sm">
                        <span>{tier}</span>
                        <Badge variant="secondary">{count}</Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Analyzer Usage</CardTitle>
                  <CardDescription>Rule-based vs future ML analyzers</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(analytics.analyzer_distribution).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-sm">
                      <span className="font-mono">{type}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Analyses</CardTitle>
                <CardDescription>Last 10 profile intelligence runs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4">Time</th>
                        <th className="pb-2 pr-4">Admission</th>
                        <th className="pb-2 pr-4">Scholarship</th>
                        <th className="pb-2 pr-4">Employability</th>
                        <th className="pb-2 pr-4">Tier</th>
                        <th className="pb-2 pr-4">Analyzer</th>
                        <th className="pb-2">Cache</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.recent_analyses.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-4 text-muted-foreground">
                            No analyses recorded yet
                          </td>
                        </tr>
                      ) : (
                        analytics.recent_analyses.map((row) => (
                          <tr key={row.id} className="border-b">
                            <td className="py-2 pr-4 font-mono text-xs">
                              {new Date(row.created_at).toLocaleString()}
                            </td>
                            <td className="py-2 pr-4">{row.admission_score}</td>
                            <td className="py-2 pr-4">{row.scholarship_score}</td>
                            <td className="py-2 pr-4">{row.employability_score}</td>
                            <td className="py-2 pr-4 max-w-[180px] truncate" title={row.tier ?? ""}>
                              {row.tier ?? "—"}
                            </td>
                            <td className="py-2 pr-4 font-mono text-xs">{row.analyzer_type}</td>
                            <td className="py-2">
                              <Badge variant={row.cache_hit ? "default" : "secondary"}>
                                {row.cache_hit ? "hit" : "miss"}
                              </Badge>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}

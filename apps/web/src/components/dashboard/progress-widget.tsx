"use client";

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApplications } from "@/hooks/use-queries";

const STATUS_COLORS: Record<string, string> = {
  planning: "var(--chart-1)",
  in_progress: "var(--chart-2)",
  submitted: "var(--chart-3)",
  accepted: "var(--chart-4)",
  rejected: "var(--chart-5)",
};

export function ProgressOverviewWidget() {
  const { data } = useApplications();
  const statusCounts: Record<string, number> = {};
  (data ?? []).forEach((a) => {
    statusCounts[a.status] = (statusCounts[a.status] ?? 0) + 1;
  });
  const chartData = Object.entries(statusCounts).map(([status, count]) => ({
    status: status.replace("_", " "),
    count,
    fill: STATUS_COLORS[status] ?? "var(--chart-1)",
  }));

  return (
    <Card className="glass lg:col-span-2">
      <CardHeader>
        <CardTitle className="text-sm font-medium">Progress Overview</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <p className="text-sm text-muted-foreground">Start an application to track progress.</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} aria-label="Application progress by status">
              <XAxis dataKey="status" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

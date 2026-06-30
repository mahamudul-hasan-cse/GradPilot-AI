"use client";

import { Lightbulb } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfileAnalysis } from "@/hooks/use-queries";

export function AIInsightsWidget() {
  const { data, isLoading, isError } = useProfileAnalysis();
  const insights = data?.recommended_actions ?? data?.weaknesses ?? [];

  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">AI Insights</CardTitle>
        <Lightbulb className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        ) : isError || insights.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Run a profile analysis to get personalized AI insights.
          </p>
        ) : (
          <ul className="space-y-2" role="list">
            {insights.slice(0, 3).map((item, i) => (
              <li key={i} className="text-sm text-muted-foreground before:mr-2 before:content-['•']">
                {item}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

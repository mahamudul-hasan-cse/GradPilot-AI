"use client";

import { TrendingUp } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfileAnalysis } from "@/hooks/use-queries";

export function ReadinessWidget() {
  const { data, isLoading, isError } = useProfileAnalysis();
  const score = data?.readiness_score ?? 0;

  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Admission Readiness</CardTitle>
        <TrendingUp className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-10 w-20" />
        ) : isError ? (
          <p className="text-2xl font-bold text-muted-foreground">—</p>
        ) : (
          <>
            <p className="text-3xl font-bold">{Math.round(score)}%</p>
            <Progress value={score} className="mt-3" aria-label={`Readiness score ${score}%`} />
          </>
        )}
      </CardContent>
    </Card>
  );
}

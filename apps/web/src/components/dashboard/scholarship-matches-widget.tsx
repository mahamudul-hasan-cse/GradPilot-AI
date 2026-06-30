"use client";

import { Wallet } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { useScholarshipMatches } from "@/hooks/use-queries";

export function ScholarshipMatchesWidget() {
  const { data, isLoading, isError } = useScholarshipMatches();
  const matches = data?.matches ?? [];

  return (
    <Card className="glass lg:col-span-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium">Scholarship Matches</CardTitle>
        <Link href="/scholarships" className="text-xs text-primary hover:underline">
          Explore
        </Link>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : isError || matches.length === 0 ? (
          <EmptyState
            icon={Wallet}
            title="No scholarships found"
            description="Update your profile and we'll surface funding opportunities."
            action={{ label: "Find scholarships", href: "/scholarships" }}
            className="border-0 p-4"
          />
        ) : (
          <ul className="space-y-3" role="list">
            {matches.slice(0, 4).map((m) => (
              <li key={m.scholarship.id} className="flex items-center justify-between rounded-lg border p-3">
                <p className="font-medium text-sm line-clamp-1">{m.scholarship.title}</p>
                <Badge variant="secondary">{Math.round(m.score.scholarship_score)}%</Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

"use client";

import { GraduationCap } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { useUniversityMatches } from "@/hooks/use-queries";

export function UniversityMatchesWidget() {
  const { data, isLoading, isError } = useUniversityMatches();
  const matches = data?.recommendations ?? [];

  return (
    <Card className="glass lg:col-span-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium">University Matches</CardTitle>
        <Link href="/universities" className="text-xs text-primary hover:underline">
          View all
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
            icon={GraduationCap}
            title="No matches yet"
            description="Complete your profile to get personalized university recommendations."
            action={{ label: "Build profile", href: "/profile" }}
            className="border-0 p-4"
          />
        ) : (
          <ul className="space-y-3" role="list">
            {matches.slice(0, 4).map((m) => (
              <li key={m.university_id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium text-sm">{m.university_name}</p>
                  <p className="text-xs text-muted-foreground">{m.country}</p>
                </div>
                <Badge variant="secondary">{Math.round(m.match_score * 100)}% match</Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

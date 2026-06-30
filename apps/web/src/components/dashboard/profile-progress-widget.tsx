"use client";

import Link from "next/link";
import { CheckCircle2, CircleDashed, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfile } from "@/hooks/use-queries";

const PROFILE_FIELDS = [
  { key: "nationality", label: "Personal details" },
  { key: "target_degree", label: "Target degree" },
  { key: "field_of_study", label: "Field of study" },
  { key: "gpa", label: "Academic score" },
  { key: "english", label: "English test" },
  { key: "budget_max", label: "Budget" },
  { key: "target_countries", label: "Target countries" },
  { key: "bio", label: "Profile summary" },
] as const;

function hasValue(value: unknown) {
  if (Array.isArray(value)) return value.length > 0;
  return value !== null && value !== undefined && value !== "";
}

export function ProfileProgressWidget() {
  const { data: profile, isLoading } = useProfile();

  const completed = PROFILE_FIELDS.filter((field) => {
    if (!profile) return false;
    if (field.key === "english") {
      return hasValue(profile.test_scores?.ielts) || hasValue(profile.test_scores?.toefl);
    }
    return hasValue(profile[field.key as keyof typeof profile]);
  });
  const percentage = Math.round((completed.length / PROFILE_FIELDS.length) * 100);
  const nextField = PROFILE_FIELDS.find((field) => !completed.includes(field));

  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Profile Progress</CardTitle>
        <UserRound className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-4 w-40" />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <p className="text-3xl font-bold">{percentage}%</p>
              <Progress value={percentage} className="mt-3" aria-label={`Profile completion ${percentage}%`} />
            </div>

            <div className="space-y-2">
              {PROFILE_FIELDS.slice(0, 4).map((field) => {
                const done = completed.includes(field);
                return (
                  <div key={field.key} className="flex items-center gap-2 text-sm">
                    {done ? (
                      <CheckCircle2 className="h-4 w-4 text-success" aria-hidden />
                    ) : (
                      <CircleDashed className="h-4 w-4 text-muted-foreground" aria-hidden />
                    )}
                    <span className={done ? "text-muted-foreground" : undefined}>{field.label}</span>
                  </div>
                );
              })}
            </div>

            <Button asChild size="sm" variant={nextField ? "default" : "outline"}>
              <Link href="/profile">{nextField ? `Complete ${nextField.label}` : "Review profile"}</Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

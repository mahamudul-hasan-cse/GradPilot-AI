"use client";

import { useCallback, useRef } from "react";
import { GraduationCap, MapPin, Search } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useUniversitiesInfinite } from "@/hooks/use-queries";
import { useState } from "react";

export default function UniversitiesPage() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const observer = useRef<IntersectionObserver | null>(null);

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } = useUniversitiesInfinite(search);

  const lastRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (isFetchingNextPage) return;
      if (observer.current) observer.current.disconnect();
      observer.current = new IntersectionObserver((entries) => {
        if (entries[0]?.isIntersecting && hasNextPage) fetchNextPage();
      });
      if (node) observer.current.observe(node);
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage],
  );

  const universities = data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <AppShell title="University Explorer" description="Discover programs matched to your profile">
      <div className="mb-6 flex gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            placeholder="Search universities..."
            className="pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(query)}
            aria-label="Search universities"
          />
        </div>
      </div>

      {isLoading ? (
        <ListSkeleton />
      ) : universities.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="No universities found"
          description="Try a different search term or check back after data ingestion."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {universities.map((uni, i) => (
            <div key={uni.id} ref={i === universities.length - 1 ? lastRef : undefined}>
              <Card className="h-full transition-shadow hover:shadow-md">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base line-clamp-2">{uni.name}</CardTitle>
                  {uni.ranking && <Badge variant="secondary">#{uni.ranking}</Badge>}
                </div>
                <CardDescription className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" aria-hidden />
                  {[uni.city, uni.country].filter(Boolean).join(", ")}
                </CardDescription>
              </CardHeader>
              {uni.description && (
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-3">{uni.description}</p>
                </CardContent>
              )}
              </Card>
            </div>
          ))}
        </div>
      )}

      {isFetchingNextPage && <ListSkeleton count={2} />}
    </AppShell>
  );
}

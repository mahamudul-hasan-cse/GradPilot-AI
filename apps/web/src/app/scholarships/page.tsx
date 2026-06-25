"use client";

import { useCallback, useRef, useState } from "react";
import { Search, Wallet } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useScholarshipsInfinite } from "@/hooks/use-queries";

export default function ScholarshipsPage() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const observer = useRef<IntersectionObserver | null>(null);

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } = useScholarshipsInfinite(search);
  const scholarships = data?.pages.flatMap((p) => p.items) ?? [];

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

  return (
    <AppShell title="Scholarship Explorer" description="Find funding opportunities worldwide">
      <div className="mb-6 relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <Input
          placeholder="Search scholarships..."
          className="pl-9"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setSearch(query)}
          aria-label="Search scholarships"
        />
      </div>

      {isLoading ? (
        <ListSkeleton />
      ) : scholarships.length === 0 ? (
        <EmptyState icon={Wallet} title="No scholarships found" description="Try adjusting your search." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {scholarships.map((s, i) => (
            <div key={s.id} ref={i === scholarships.length - 1 ? lastRef : undefined}>
              <Card>
              <CardHeader>
                <CardTitle className="text-base">{s.title}</CardTitle>
                <CardDescription>{s.provider}{s.country ? ` · ${s.country}` : ""}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {s.amount && (
                  <Badge variant="secondary">
                    {s.currency ?? "$"}{s.amount}
                  </Badge>
                )}
                {s.deadline && <Badge variant="outline">Due {new Date(s.deadline).toLocaleDateString()}</Badge>}
              </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}
      {isFetchingNextPage && <ListSkeleton count={2} />}
    </AppShell>
  );
}

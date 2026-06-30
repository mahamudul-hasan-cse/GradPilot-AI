"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Award, Calendar, ExternalLink, Globe, Search, SlidersHorizontal, Wallet, X } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useScholarshipsInfinite } from "@/hooks/use-queries";
import type { Scholarship } from "@gradpilot/shared";

const DEGREE_FILTERS = ["All", "masters", "phd", "undergraduate"];
const FUNDING_FILTERS = ["All", "full", "partial"];

function fundingBadge(type: string | null | undefined) {
  if (type === "full") return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 text-xs">Fully Funded</Badge>;
  if (type === "partial") return <Badge variant="secondary" className="text-xs">Partial</Badge>;
  return null;
}

function ScholarshipCard({ s, onClick }: { s: Scholarship; onClick: () => void }) {
  const sc = s as any;
  return (
    <button type="button" onClick={onClick} className="group w-full text-left" aria-label={`View ${s.title} details`}>
      <Card className="h-full transition-all hover:shadow-md hover:border-primary/30">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-sm font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors">
              {s.title}
            </CardTitle>
            {fundingBadge(sc.funding_type)}
          </div>
          <p className="text-xs text-muted-foreground">{s.provider}</p>
        </CardHeader>
        <CardContent className="space-y-2.5">
          {sc.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">{sc.description}</p>
          )}
          <div className="flex flex-wrap gap-1.5">
            {s.amount && (
              <Badge variant="outline" className="text-xs gap-1">
                <Wallet className="h-2.5 w-2.5" />
                {Number(s.amount).toLocaleString()} {s.currency ?? "USD"}
              </Badge>
            )}
            {s.country && (
              <Badge variant="secondary" className="text-xs gap-1">
                <Globe className="h-2.5 w-2.5" />
                {s.country}
              </Badge>
            )}
            {sc.degree_level && (
              <Badge variant="outline" className="text-xs capitalize">
                {sc.degree_level}
              </Badge>
            )}
            {s.deadline && (
              <Badge variant="outline" className="text-xs gap-1">
                <Calendar className="h-2.5 w-2.5" />
                {new Date(s.deadline).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </button>
  );
}

function ScholarshipModal({ s, open, onClose }: { s: Scholarship | null; open: boolean; onClose: () => void }) {
  if (!s) return null;
  const sc = s as any;
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-base leading-snug">{s.title}</DialogTitle>
          <DialogDescription>{s.provider}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 text-sm">
          {sc.description && <p className="text-muted-foreground">{sc.description}</p>}

          <div className="grid grid-cols-2 gap-3">
            {s.amount && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">Award Amount</p>
                <p className="font-semibold">{Number(s.amount).toLocaleString()} {s.currency ?? "USD"}</p>
              </div>
            )}
            {s.country && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">Study Country</p>
                <p className="font-semibold">{s.country}</p>
              </div>
            )}
            {sc.degree_level && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">Degree Level</p>
                <p className="font-semibold capitalize">{sc.degree_level}</p>
              </div>
            )}
            {s.deadline && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">Application Deadline</p>
                <p className="font-semibold">{new Date(s.deadline).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</p>
              </div>
            )}
          </div>

          {sc.eligibility && (
            <div>
              <p className="mb-1.5 text-xs font-medium text-muted-foreground">Eligibility Requirements</p>
              <p className="text-sm">{sc.eligibility}</p>
            </div>
          )}

          {sc.funding_type && (
            <div className="flex items-center gap-2">
              {fundingBadge(sc.funding_type)}
              <span className="text-xs text-muted-foreground">
                {sc.funding_type === "full" ? "Covers tuition + living expenses" : "Partial tuition support"}
              </span>
            </div>
          )}

          {sc.application_url && (
            <Button asChild className="w-full gap-2">
              <a href={sc.application_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
                Apply Now
              </a>
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function ScholarshipsPage() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [degreeFilter, setDegreeFilter] = useState("All");
  const [fundingFilter, setFundingFilter] = useState("All");
  const [showFilters, setShowFilters] = useState(false);
  const [selected, setSelected] = useState<Scholarship | null>(null);
  const observer = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setSearch(query), 350);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } = useScholarshipsInfinite(search);
  const allScholarships = data?.pages.flatMap((p) => p.items) ?? [];

  // Client-side filter by degree/funding type (API doesn't support these params yet)
  const scholarships = allScholarships.filter((s) => {
    const sc = s as any;
    if (degreeFilter !== "All" && sc.degree_level !== degreeFilter) return false;
    if (fundingFilter !== "All" && sc.funding_type !== fundingFilter) return false;
    return true;
  });

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

  const activeFilters = (degreeFilter !== "All" ? 1 : 0) + (fundingFilter !== "All" ? 1 : 0);

  return (
    <AppShell title="Scholarship Explorer" description="Find real funding opportunities worldwide">
      {/* Search bar */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            placeholder="Search scholarships by name, country, or provider…"
            className="pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search scholarships"
          />
          {query && (
            <button type="button" onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button
          variant={showFilters ? "default" : "outline"}
          size="sm"
          onClick={() => setShowFilters((v) => !v)}
          className="gap-1.5 shrink-0"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilters > 0 && <span className="ml-1 rounded-full bg-primary-foreground text-primary px-1.5 text-xs font-semibold">{activeFilters}</span>}
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="mb-5 space-y-3">
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">Degree Level</p>
            <div className="flex flex-wrap gap-2">
              {DEGREE_FILTERS.map((d) => (
                <button key={d} type="button" onClick={() => setDegreeFilter(d)}
                  className={`rounded-full border px-3 py-1 text-xs capitalize transition-colors ${degreeFilter === d ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:bg-muted"}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">Funding Type</p>
            <div className="flex flex-wrap gap-2">
              {FUNDING_FILTERS.map((f) => (
                <button key={f} type="button" onClick={() => setFundingFilter(f)}
                  className={`rounded-full border px-3 py-1 text-xs capitalize transition-colors ${fundingFilter === f ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:bg-muted"}`}>
                  {f === "full" ? "Fully Funded" : f === "partial" ? "Partial" : f}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {!isLoading && scholarships.length > 0 && (
        <p className="mb-4 text-sm text-muted-foreground">
          {scholarships.length} {scholarships.length === 1 ? "scholarship" : "scholarships"} found
          {" · "}
          <span className="text-foreground">Click any card for details & application link</span>
        </p>
      )}

      {isLoading ? (
        <ListSkeleton />
      ) : scholarships.length === 0 ? (
        <EmptyState icon={Award} title="No scholarships found" description="Try adjusting your search or filters."
          action={(search || activeFilters > 0) ? { label: "Clear all filters", onClick: () => { setQuery(""); setDegreeFilter("All"); setFundingFilter("All"); } } : undefined} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {scholarships.map((s, i) => (
            <div key={s.id} ref={i === scholarships.length - 1 ? lastRef : undefined}>
              <ScholarshipCard s={s} onClick={() => setSelected(s)} />
            </div>
          ))}
        </div>
      )}

      {isFetchingNextPage && <ListSkeleton count={3} />}

      <ScholarshipModal s={selected} open={!!selected} onClose={() => setSelected(null)} />
    </AppShell>
  );
}

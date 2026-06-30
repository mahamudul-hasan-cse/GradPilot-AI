"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  BookOpen,
  DollarSign,
  ExternalLink,
  GraduationCap,
  MapPin,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useUniversitiesInfinite } from "@/hooks/use-queries";
import type { University } from "@gradpilot/shared";

const COUNTRIES = [
  "United States",
  "United Kingdom",
  "Canada",
  "Australia",
  "Germany",
  "Netherlands",
  "Singapore",
  "Japan",
  "Ireland",
  "Switzerland",
  "New Zealand",
];

function tierLabel(ranking: number | undefined | null): { label: string; color: string } {
  if (!ranking) return { label: "Unranked", color: "secondary" };
  if (ranking <= 20) return { label: "Elite", color: "destructive" };
  if (ranking <= 50) return { label: "Top 50", color: "warning" };
  if (ranking <= 100) return { label: "Top 100", color: "success" };
  return { label: "Top 200", color: "secondary" };
}

function UniversityCard({
  uni,
  onClick,
}: {
  uni: University;
  onClick: () => void;
}) {
  const tier = tierLabel(uni.ranking);
  return (
    <button
      type="button"
      onClick={onClick}
      className="group w-full text-left"
      aria-label={`View ${uni.name} details`}
    >
      <Card className="h-full transition-all hover:shadow-md hover:border-primary/30 group-focus-visible:ring-2 group-focus-visible:ring-primary">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base leading-snug line-clamp-2 group-hover:text-primary transition-colors">
              {uni.name}
            </CardTitle>
            {uni.ranking && (
              <Badge variant="secondary" className="shrink-0 text-xs">
                #{uni.ranking}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3" aria-hidden />
            {[uni.city, uni.country].filter(Boolean).join(", ")}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {uni.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">{uni.description}</p>
          )}
          <div className="flex flex-wrap gap-1.5">
            <Badge
              variant={tier.color as "secondary" | "destructive" | "outline"}
              className="text-xs"
            >
              {tier.label}
            </Badge>
            {(uni as any).minimum_ielts && (
              <Badge variant="outline" className="text-xs">
                IELTS {(uni as any).minimum_ielts}+
              </Badge>
            )}
            {(uni as any).tuition_fee && (
              <Badge variant="outline" className="text-xs">
                ~{Number((uni as any).tuition_fee).toLocaleString()} {(uni as any).currency ?? "USD"}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </button>
  );
}

function UniversityModal({
  uni,
  open,
  onClose,
}: {
  uni: University | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!uni) return null;
  const u = uni as any;
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-lg leading-snug">{uni.name}</DialogTitle>
          <DialogDescription className="flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" />
            {[uni.city, uni.country].filter(Boolean).join(", ")}
            {uni.ranking && <span className="ml-2 text-primary">Ranked #{uni.ranking}</span>}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm">
          {uni.description && <p className="text-muted-foreground">{uni.description}</p>}

          <div className="grid grid-cols-2 gap-3">
            {u.tuition_fee && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground flex items-center gap-1 mb-1">
                  <DollarSign className="h-3 w-3" /> Tuition / Year
                </p>
                <p className="font-semibold">
                  {Number(u.tuition_fee).toLocaleString()} {u.currency ?? "USD"}
                </p>
              </div>
            )}
            {u.minimum_ielts && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">Min. IELTS</p>
                <p className="font-semibold">{u.minimum_ielts}</p>
              </div>
            )}
            {u.minimum_gpa && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">Min. GPA</p>
                <p className="font-semibold">{u.minimum_gpa} / 4.0</p>
              </div>
            )}
            {uni.ranking && (
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground mb-1">World Ranking</p>
                <p className="font-semibold">#{uni.ranking}</p>
              </div>
            )}
          </div>

          {u.programs?.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground flex items-center gap-1">
                <BookOpen className="h-3.5 w-3.5" /> Programs Offered
              </p>
              <div className="flex flex-wrap gap-1.5">
                {u.programs.map((p: string) => (
                  <Badge key={p} variant="secondary" className="text-xs">
                    {p}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {uni.website && (
            <Button asChild className="w-full gap-2">
              <a href={uni.website} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
                Visit Official Website
              </a>
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function UniversitiesPage() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState<string | undefined>();
  const [selected, setSelected] = useState<University | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const observer = useRef<IntersectionObserver | null>(null);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setSearch(query), 350);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useUniversitiesInfinite(search, country);

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
    <AppShell
      title="University Explorer"
      description="Discover and compare universities worldwide"
    >
      {/* Search + filter bar */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            placeholder="Search universities by name, country, or program…"
            className="pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search universities"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
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
          {country && <span className="ml-1 rounded-full bg-primary-foreground text-primary px-1.5 text-xs font-semibold">{1}</span>}
        </Button>
      </div>

      {/* Country filter pills */}
      {showFilters && (
        <div className="mb-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setCountry(undefined)}
            className={`rounded-full border px-3 py-1 text-xs transition-colors ${!country ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:bg-muted"}`}
          >
            All Countries
          </button>
          {COUNTRIES.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCountry(country === c ? undefined : c)}
              className={`rounded-full border px-3 py-1 text-xs transition-colors ${country === c ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:bg-muted"}`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* Results summary */}
      {!isLoading && universities.length > 0 && (
        <p className="mb-4 text-sm text-muted-foreground">
          {universities.length} {universities.length === 1 ? "university" : "universities"} found
          {country && ` in ${country}`}
          {search && ` matching "${search}"`}
          {" · "}
          <span className="text-foreground">Click any card for details</span>
        </p>
      )}

      {isLoading ? (
        <ListSkeleton />
      ) : universities.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="No universities found"
          description="Try a different search term or remove filters."
          action={
            (search || country)
              ? { label: "Clear filters", onClick: () => { setQuery(""); setCountry(undefined); } }
              : undefined
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {universities.map((uni, i) => (
            <div key={uni.id} ref={i === universities.length - 1 ? lastRef : undefined}>
              <UniversityCard uni={uni} onClick={() => setSelected(uni)} />
            </div>
          ))}
        </div>
      )}

      {isFetchingNextPage && <ListSkeleton count={3} />}

      <UniversityModal uni={selected} open={!!selected} onClose={() => setSelected(null)} />
    </AppShell>
  );
}

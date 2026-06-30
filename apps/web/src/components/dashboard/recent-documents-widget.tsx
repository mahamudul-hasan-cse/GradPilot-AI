"use client";

import Link from "next/link";
import { ArrowRight, FileText, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDocuments } from "@/hooks/use-queries";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function documentLabel(type: string | null, fileName: string) {
  if (type) return type.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
  return fileName;
}

export function RecentDocumentsWidget() {
  const { data, isLoading } = useDocuments();
  const recent = [...(data ?? [])]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3);

  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Recent Documents</CardTitle>
        <FileText className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
          </div>
        ) : recent.length === 0 ? (
          <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
            Upload IELTS, CV, or transcript files to unlock better AI guidance.
          </div>
        ) : (
          <div className="space-y-3">
            {recent.map((document) => (
              <div key={document.id} className="rounded-xl border bg-background/50 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {documentLabel(document.classified_type ?? document.document_type, document.file_name)}
                    </p>
                    <p className="mt-1 truncate text-xs text-muted-foreground">
                      {document.file_name} • {formatDate(document.created_at)}
                    </p>
                  </div>
                  <Badge variant={document.validation_result?.is_valid ? "success" : "outline"}>
                    {document.validation_result?.is_valid ? (
                      <ShieldCheck className="mr-1 h-3 w-3" aria-hidden />
                    ) : null}
                    {document.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}

        <Button asChild variant="ghost" size="sm" className="mt-4 px-0">
          <Link href="/documents">
            Manage documents <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

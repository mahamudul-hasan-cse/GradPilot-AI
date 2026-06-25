"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, Upload } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DOCUMENT_TYPES } from "@/lib/constants";
import { useDocuments, useUploadDocument } from "@/hooks/use-queries";

export default function DocumentsPage() {
  const { data, isLoading } = useDocuments();
  const upload = useUploadDocument();
  const [docType, setDocType] = useState<string>("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) upload.mutate({ file, documentType: docType || undefined });
      e.target.value = "";
    },
    [upload, docType],
  );

  return (
    <AppShell title="Documents" description="Upload and manage admission documents">
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Select value={docType} onValueChange={setDocType}>
          <SelectTrigger className="w-[200px]" aria-label="Document type">
            <SelectValue placeholder="Document type" />
          </SelectTrigger>
          <SelectContent>
            {DOCUMENT_TYPES.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <input ref={fileRef} type="file" className="hidden" onChange={handleUpload} accept=".pdf,.png,.jpg,.jpeg" />
        <Button onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
          <Upload className="h-4 w-4" aria-hidden />
          Upload document
        </Button>
      </div>

      {isLoading ? (
        <ListSkeleton />
      ) : !data?.length ? (
        <EmptyState
          icon={FileText}
          title="No documents uploaded"
          description="Upload passports, transcripts, test scores, and more for intelligent extraction."
          action={{ label: "Upload document", onClick: () => fileRef.current?.click() }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.map((doc) => (
            <Card key={doc.id}>
              <CardHeader>
                <CardTitle className="text-base line-clamp-1">{doc.file_name}</CardTitle>
                <CardDescription>{doc.classified_type ?? doc.document_type ?? "Unclassified"}</CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <Badge variant={doc.status === "validated" ? "success" : "secondary"}>{doc.status}</Badge>
                {doc.confidence_score != null && (
                  <span className="text-xs text-muted-foreground">
                    {Math.round(doc.confidence_score * 100)}% confidence
                  </span>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}

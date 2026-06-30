"use client";

import { FileText, Send, CheckCircle, Clock } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApplications, useDocuments } from "@/hooks/use-queries";

export function ApplicationStatsWidget() {
  const { data: apps } = useApplications();
  const { data: docs } = useDocuments();

  const stats = [
    { label: "Applications", value: apps?.length ?? 0, icon: Send },
    { label: "Documents", value: docs?.length ?? 0, icon: FileText },
    { label: "Submitted", value: apps?.filter((a) => a.status === "submitted").length ?? 0, icon: CheckCircle },
    { label: "In Progress", value: apps?.filter((a) => ["planning", "preparing", "ready"].includes(a.status)).length ?? 0, icon: Clock },
  ];

  return (
    <Card className="glass">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Application Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {stats.map((s) => (
            <div key={s.label} className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                <s.icon className="h-4 w-4 text-muted-foreground" aria-hidden />
              </div>
              <div>
                <p className="text-2xl font-bold">{s.value}</p>
                <p className="text-xs text-muted-foreground">{s.label}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

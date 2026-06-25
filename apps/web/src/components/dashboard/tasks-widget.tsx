"use client";

import { CheckCircle2, Circle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const DEFAULT_TASKS = [
  { id: "1", title: "Complete student profile", done: false },
  { id: "2", title: "Upload IELTS score report", done: false },
  { id: "3", title: "Review university shortlist", done: false },
];

export function TasksWidget({ tasks = DEFAULT_TASKS }: { tasks?: Array<{ id: string; title: string; done: boolean }> }) {
  return (
    <Card className="glass">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Today&apos;s Tasks</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2" role="list">
          {tasks.map((task) => (
            <li key={task.id} className="flex items-center gap-2 text-sm">
              {task.done ? (
                <CheckCircle2 className="h-4 w-4 text-success shrink-0" aria-hidden />
              ) : (
                <Circle className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden />
              )}
              <span className={cn(task.done && "text-muted-foreground line-through")}>{task.title}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export function TasksWidgetSkeleton() {
  return (
    <Card>
      <CardHeader><Skeleton className="h-4 w-24" /></CardHeader>
      <CardContent><Skeleton className="h-20 w-full" /></CardContent>
    </Card>
  );
}

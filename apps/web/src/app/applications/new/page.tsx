"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

export default function NewApplicationPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [deadline, setDeadline] = useState("");

  const createApplication = useMutation({
    mutationFn: () =>
      api.applications.create(session!.accessToken, {
        title: title || "Application",
        notes: notes || null,
        status: "planning",
        deadline: deadline || undefined,
      }),
    onSuccess: (application) => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Application created");
      router.push(`/applications/${application.id}`);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <AppShell title="New Application" description="Create an application workspace">
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Application details</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              if (!session?.accessToken) return;
              createApplication.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Example: University of Toronto MSc CS"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="deadline">Deadline</Label>
              <Input
                id="deadline"
                type="date"
                value={deadline}
                onChange={(event) => setDeadline(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Program, intake, scholarship notes, or next step"
              />
            </div>
            <Button type="submit" disabled={createApplication.isPending || !session?.accessToken}>
              {createApplication.isPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
              Create application
            </Button>
          </form>
        </CardContent>
      </Card>
    </AppShell>
  );
}

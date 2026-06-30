"use client";

import Link from "next/link";
import { Bot, FileUp, GraduationCap, MessageSquareText, PenLine, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ACTIONS = [
  {
    href: "/advisor",
    title: "Ask AI Advisor",
    description: "Get strategy for countries, universities, visas, or scholarships.",
    icon: MessageSquareText,
  },
  {
    href: "/universities",
    title: "Find Universities",
    description: "Search and compare safe, target, and ambitious options.",
    icon: Search,
  },
  {
    href: "/documents",
    title: "Upload Documents",
    description: "Add IELTS, CV, or transcript files for better recommendations.",
    icon: FileUp,
  },
  {
    href: "/scholarships",
    title: "Check Scholarships",
    description: "Find awards that match your profile and budget.",
    icon: GraduationCap,
  },
] as const;

export function AIQuickActionsWidget() {
  return (
    <Card className="glass">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">AI Quick Actions</CardTitle>
        <Bot className="h-4 w-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {ACTIONS.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="rounded-xl border bg-background/50 p-3 transition-colors hover:bg-muted/50"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <action.icon className="h-4 w-4" aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-medium">{action.title}</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>

        <Button asChild className="mt-4 w-full" variant="outline">
          <Link href="/advisor">
            <PenLine className="h-4 w-4" aria-hidden /> Start with a profile review
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

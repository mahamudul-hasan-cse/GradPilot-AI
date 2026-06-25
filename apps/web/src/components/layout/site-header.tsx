"use client";

import Link from "next/link";
import { GraduationCap } from "lucide-react";

import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <GraduationCap className="h-5 w-5 text-primary" aria-hidden />
          GradPilot AI
        </Link>
        <nav className="hidden items-center gap-6 md:flex" aria-label="Marketing navigation">
          <Link href="/#features" className="text-sm text-muted-foreground hover:text-foreground">
            Features
          </Link>
          <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground">
            Pricing
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" size="sm" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/register">Get started</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

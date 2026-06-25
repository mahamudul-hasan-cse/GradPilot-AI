"use client";

import { AlertTriangle } from "lucide-react";
import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "@/components/ui/button";

type Props = { children: ReactNode; fallback?: ReactNode };
type State = { hasError: boolean };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="flex flex-col items-center justify-center gap-4 rounded-xl border p-12 text-center" role="alert">
            <AlertTriangle className="h-10 w-10 text-destructive" aria-hidden />
            <div>
              <h2 className="text-lg font-semibold">Something went wrong</h2>
              <p className="mt-1 text-sm text-muted-foreground">An unexpected error occurred. Please try again.</p>
            </div>
            <Button onClick={() => this.setState({ hasError: false })}>Try again</Button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}

import type { Metadata } from "next";
import { Check } from "lucide-react";
import Link from "next/link";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { PRICING_PLANS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Simple, transparent pricing for your study abroad journey.",
};

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main className="mx-auto max-w-6xl px-4 py-20">
        <div className="mb-16 text-center">
          <Badge variant="secondary" className="mb-4">Pricing</Badge>
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">Plans that grow with you</h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Start free. Upgrade when you need the full AI copilot.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {PRICING_PLANS.map((plan) => (
            <Card
              key={plan.name}
              className={cn("relative flex flex-col", plan.highlighted && "border-primary shadow-glow")}
            >
              {plan.highlighted && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most popular</Badge>
              )}
              <CardHeader>
                <CardTitle>{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
                <div className="pt-4">
                  <span className="text-4xl font-bold">${plan.price}</span>
                  {plan.price > 0 && <span className="text-muted-foreground">/month</span>}
                </div>
              </CardHeader>
              <CardContent className="flex-1">
                <ul className="space-y-3" role="list">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
                      {f}
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button className="w-full" variant={plan.highlighted ? "default" : "outline"} asChild>
                  <Link href="/register">{plan.cta}</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}

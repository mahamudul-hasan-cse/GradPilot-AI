"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  Bot,
  FileText,
  GraduationCap,
  Search,
  Shield,
  Sparkles,
  Wallet,
  Zap,
} from "lucide-react";
import Link from "next/link";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  { icon: Search, title: "University Explorer", description: "Semantic search across global programs matched to your profile." },
  { icon: Wallet, title: "Scholarship Matching", description: "AI-ranked funding opportunities with deadline tracking." },
  { icon: Bot, title: "AI Advisor", description: "Personalized guidance powered by your Student Digital Twin." },
  { icon: FileText, title: "Document Intelligence", description: "OCR, extraction, and validation for admission documents." },
  { icon: Sparkles, title: "Application Workspace", description: "Tasks, deadlines, and progress tracking in one place." },
  { icon: Shield, title: "Profile Intelligence", description: "Readiness scores and gap analysis for competitive programs." },
];

const stats = [
  { value: "10K+", label: "Universities indexed" },
  { value: "5K+", label: "Scholarships tracked" },
  { value: "92%", label: "User satisfaction" },
  { value: "<2s", label: "AI response time" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 grid-pattern opacity-40" aria-hidden />
          <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" aria-hidden />
          <div className="relative mx-auto max-w-6xl px-4 py-24 md:py-32">
            <motion.div
              className="mx-auto max-w-3xl text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Badge variant="secondary" className="mb-4">
                <Zap className="mr-1 h-3 w-3" aria-hidden />
                AI-powered study abroad platform
              </Badge>
              <h1 className="text-4xl font-bold tracking-tight md:text-6xl lg:text-7xl">
                Navigate your <span className="gradient-text">global education</span> journey
              </h1>
              <p className="mt-6 text-lg text-muted-foreground md:text-xl">
                Discover universities, match scholarships, get AI guidance, and manage applications —
                all powered by your Student Digital Twin.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Button size="lg" asChild className="shadow-glow">
                  <Link href="/register">
                    Start free <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/pricing">View pricing</Link>
                </Button>
              </div>
            </motion.div>
          </div>
        </section>

        <section className="border-y bg-muted/30 py-12">
          <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 px-4 md:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="text-2xl font-bold md:text-3xl">{s.value}</p>
                <p className="text-sm text-muted-foreground">{s.label}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="py-24">
          <div className="mx-auto max-w-6xl px-4">
            <div className="mb-16 text-center">
              <GraduationCap className="mx-auto mb-4 h-8 w-8 text-primary" aria-hidden />
              <h2 className="text-3xl font-bold md:text-4xl">Everything in one copilot</h2>
              <p className="mt-3 text-muted-foreground">Built for ambitious students applying to top programs worldwide.</p>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {features.map((f, i) => (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                >
                  <Card className="h-full transition-shadow hover:shadow-md">
                    <CardHeader>
                      <f.icon className="mb-2 h-6 w-6 text-primary" aria-hidden />
                      <CardTitle>{f.title}</CardTitle>
                      <CardDescription>{f.description}</CardDescription>
                    </CardHeader>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t bg-primary/5 py-24">
          <div className="mx-auto max-w-3xl px-4 text-center">
            <h2 className="text-3xl font-bold">Ready to take flight?</h2>
            <p className="mt-4 text-muted-foreground">Join thousands of students using AI to land their dream programs.</p>
            <Button size="lg" className="mt-8" asChild>
              <Link href="/register">Create your free account</Link>
            </Button>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

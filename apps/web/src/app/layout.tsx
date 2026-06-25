import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { Providers } from "@/components/providers";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "GradPilot AI — Study Abroad Copilot",
    template: "%s | GradPilot AI",
  },
  description:
    "University discovery, scholarship matching, AI guidance, document intelligence, and application tracking for students studying abroad.",
  keywords: ["study abroad", "university", "scholarship", "AI advisor", "graduate school"],
  openGraph: {
    title: "GradPilot AI",
    description: "Your AI copilot for global education",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

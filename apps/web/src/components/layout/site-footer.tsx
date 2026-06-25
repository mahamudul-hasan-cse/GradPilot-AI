import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t py-12">
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">© {new Date().getFullYear()} GradPilot AI. All rights reserved.</p>
          <nav className="flex gap-6" aria-label="Footer navigation">
            <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground">
              Pricing
            </Link>
            <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground">
              Sign in
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}

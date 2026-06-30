export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { href: "/profile", label: "Profile", icon: "User" },
  { href: "/universities", label: "Universities", icon: "GraduationCap" },
  { href: "/scholarships", label: "Scholarships", icon: "Wallet" },
  { href: "/advisor", label: "AI Advisor", icon: "Bot" },
  { href: "/planner", label: "Planner", icon: "CalendarCheck" },
  { href: "/applications", label: "Applications", icon: "FolderOpen" },
  { href: "/documents", label: "Documents", icon: "FileText" },
  { href: "/timeline", label: "Timeline", icon: "GitBranch" },
  { href: "/notifications", label: "Notifications", icon: "Bell" },
  { href: "/settings", label: "Settings", icon: "Settings" },
] as const;

export const DOCUMENT_TYPES = [
  { value: "passport", label: "Passport" },
  { value: "transcript", label: "Transcript" },
  { value: "degree_certificate", label: "Degree Certificate" },
  { value: "cv", label: "CV / Resume" },
  { value: "ielts_trf", label: "IELTS TRF" },
  { value: "toefl", label: "TOEFL Score Report" },
  { value: "gre", label: "GRE Score Report" },
  { value: "lor", label: "Recommendation Letter" },
  { value: "sop", label: "Statement of Purpose" },
] as const;

export const PRICING_PLANS = [
  {
    name: "Starter",
    price: 0,
    description: "Essential tools to begin your study abroad journey.",
    features: ["University search", "Profile builder", "3 AI advisor messages/day", "1 application workspace"],
    cta: "Start free",
    highlighted: false,
  },
  {
    name: "Pro",
    price: 19,
    description: "Full AI copilot for serious applicants.",
    features: [
      "Unlimited AI advisor",
      "Scholarship matching",
      "Document intelligence",
      "5 application workspaces",
      "Priority support",
    ],
    cta: "Upgrade to Pro",
    highlighted: true,
  },
  {
    name: "Premium",
    price: 49,
    description: "White-glove guidance for competitive programs.",
    features: [
      "Everything in Pro",
      "SOP co-pilot",
      "1:1 advisor sessions",
      "Unlimited workspaces",
      "Early access features",
    ],
    cta: "Contact sales",
    highlighted: false,
  },
] as const;

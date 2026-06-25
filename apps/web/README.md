# GradPilot Web

Production-grade Next.js 15 frontend for GradPilot AI.

## Stack

- **Next.js 15** (App Router) + TypeScript
- **Tailwind CSS v4** with design tokens (light/dark)
- **shadcn/ui** primitives (Radix + CVA)
- **TanStack Query** — server state, infinite scroll, optimistic updates
- **Zustand** — UI state (sidebar, notifications)
- **React Hook Form + Zod** — form validation
- **NextAuth v5** — JWT credentials via backend API
- **Framer Motion** — landing & chat animations
- **Recharts** — dashboard charts
- **React Flow** — timeline visualization

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/pricing` | Pricing tiers |
| `/login`, `/register` | Authentication |
| `/dashboard` | Command center with 8 widgets |
| `/profile` | Student profile builder |
| `/universities` | University explorer (infinite scroll) |
| `/scholarships` | Scholarship explorer |
| `/advisor` | AI chat advisor |
| `/applications` | Application workspaces |
| `/documents` | Document intelligence uploads |
| `/timeline` | React Flow journey timeline |
| `/notifications` | Activity feed |
| `/settings` | Account & preferences |

## Setup

```bash
cp .env.example .env.local
# Set AUTH_SECRET (openssl rand -base64 32)

npm run dev
```

Ensure the API is running at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Architecture

```
src/
├── app/              # App Router pages
├── components/
│   ├── ui/           # shadcn primitives (Storybook-ready)
│   ├── layout/       # App shell, sidebar, marketing header
│   ├── dashboard/    # Dashboard widgets
│   ├── shared/       # Empty states, skeletons, error boundary
│   └── providers/    # Query, session, theme
├── hooks/            # use-queries, use-auth
├── lib/              # API client, auth, constants
├── stores/           # Zustand stores
└── types/            # NextAuth augmentation
```

## Features

- Responsive layout with collapsible sidebar
- Dark mode (class-based, system preference)
- WCAG: focus rings, aria labels, semantic HTML
- Loading skeletons & empty states
- Error boundaries (app-level + route error.tsx)
- Protected routes via middleware
- Optimistic document uploads
- Infinite scroll for universities/scholarships

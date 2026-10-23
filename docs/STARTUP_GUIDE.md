# GradPilot Startup Guide

Step-by-step instructions to run GradPilot locally without Docker.

## Before you start

1. Copy `.env.example` → `.env` at the repo root.
2. Copy `apps/web/.env.example` → `apps/web/.env.local`.
3. Set your own `OPENROUTER_API_KEY` (preferred) or `GEMINI_API_KEY`, database URL, and random secrets.
4. **Never commit `.env` or `.env.local`** — they are gitignored.

---

## Backend

From the repository root:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_universities_scholarships.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_universities_scholarships.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the helper scripts from the repo root:

```bat
scripts\setup_backend.bat
scripts\run_backend.bat
```

---

## Frontend

From the repository root:

```bash
npm install
npm run dev
```

Windows:

```bat
scripts\setup_frontend.bat
scripts\run_frontend.bat
```

---

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

---

## Database

### Local PostgreSQL

Create a database and user, then set in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://gradpilot:YOUR_PASSWORD@localhost:5432/gradpilot
```

### Neon (cloud)

Paste your Neon connection string into `DATABASE_URL`. Standard `postgresql://` URLs are converted automatically.

---

## Required environment variables

Root `.env`:

```env
DATABASE_URL=
SECRET_KEY=
JWT_SECRET=
AUTH_SECRET=
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
UPLOAD_DIR=uploads
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Frontend `apps/web/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_V1_PREFIX=/api/v1
AUTH_SECRET=          # must match root AUTH_SECRET
AUTH_URL=http://localhost:3000
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `failed to fetch` on login | Check backend is running; verify `NEXT_PUBLIC_API_URL` in `.env.local` |
| Redirect loop on login | Clear browser cookies; ensure `AUTH_SECRET` matches in both env files |
| Empty universities/scholarships | Run `python scripts/seed_universities_scholarships.py` |
| AI advisor not responding | Set a valid `OPENROUTER_API_KEY` or `GEMINI_API_KEY` in `.env` and restart backend |
| Hydration warning in browser | Usually caused by Grammarly extension — safe to ignore |

---

## What stays local (not in Git)

- `.env`, `.env.local` — secrets
- `uploads/` — student documents
- `data/` — local PostgreSQL data directory
- `tools/` — optional local PostgreSQL binaries

See [README.md](../README.md) for the full security section.

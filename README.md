# GradPilot AI

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)

GradPilot is an AI-powered study abroad platform for international students. Students can build a profile, upload documents, discover universities and scholarships, chat with an AI advisor, generate SOP drafts, plan their application timeline, and track applications — all from one dashboard.

Runs locally with **Python + FastAPI**, **Next.js**, **PostgreSQL**, and **OpenRouter** or **Google Gemini** (no Docker required).

---
**Demo Video Link: https://youtu.be/GVCv6PTxnYU?si=4GEDcw7wUB0YRShk**
## Features

| Area | What students can do |
|------|----------------------|
| **Profile** | Save GPA, IELTS, field of study, goals; get readiness scores |
| **Universities** | Search 35+ real universities, filter by country, view details |
| **Scholarships** | Browse 40+ real scholarships with funding type and deadlines |
| **AI Advisor** | Chat with AI-powered study abroad guidance (OpenRouter or Gemini) |
| **Planner** | Personalized tasks linked to profile scores |
| **Timeline** | Visual journey of profile, documents, and application events |
| **Applications** | Kanban tracker for application stages |
| **Documents** | Upload IELTS, CV, transcripts |

---
<img width="911" height="613" alt="gradpilot" src="https://github.com/user-attachments/assets/1c1ef48a-7520-4f34-bde2-314e69d013f1" />

## Tech stack

| Layer | Stack |
|-------|--------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, React Query, Zustand, NextAuth |
| Backend | FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| AI | OpenRouter (preferred, default `openai/gpt-4o-mini`) or Google Gemini API (`gemini-2.5-flash`) |
| Production DB | [Neon PostgreSQL](https://neon.tech) (recommended) |

---

## Project structure

```
GradPilot-AI/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/shared/  # Shared TypeScript types
├── docs/             # Product & technical documentation
├── scripts/          # Setup & run scripts (Windows + Unix)
├── uploads/          # Local document uploads (gitignored)
├── .env.example      # Environment template (safe to commit)
└── README.md
```

---
## Thumbnail 
<img width="2752" height="1536" alt="Gemini_Generated_Image_8tfxxb8tfxxb8tfx" src="https://github.com/user-attachments/assets/0680ac92-e371-470a-bd25-38797e665ef5" />


## Quick start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ (local install or Neon cloud)
- An [OpenRouter API key](https://openrouter.ai/keys) or a [Google Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone and configure secrets

```bash
git clone https://github.com/mahamudul-hasan-cse/GradPilot-AI.git
cd GradPilot-AI
```

Copy environment templates and **fill in your own values**:

```bash
# Root backend config
cp .env.example .env

# Frontend config
cp apps/web/.env.example apps/web/.env.local
```

Edit `.env` and set at minimum:

- `DATABASE_URL` — your PostgreSQL connection string
- `SECRET_KEY`, `JWT_SECRET`, `AUTH_SECRET` — long random strings
- `OPENROUTER_API_KEY` (preferred) or `GEMINI_API_KEY` — at least one AI provider key

> **Important:** `AUTH_SECRET` in root `.env` must match `AUTH_SECRET` in `apps/web/.env.local`.

### 2. One-time setup

**Windows**

```bat
scripts\setup_backend.bat
scripts\setup_frontend.bat
```

**macOS / Linux**

```bash
bash scripts/setup_backend.sh
bash scripts/setup_frontend.sh
```

### 3. Seed sample data (universities & scholarships)

```bash
cd apps/api
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
python scripts/seed_universities_scholarships.py
```

### 4. Run

**Windows**

```bat
scripts\run_backend.bat
scripts\run_frontend.bat
```

**macOS / Linux**

```bash
bash scripts/run_backend.sh
bash scripts/run_frontend.sh
```

### 5. Open the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

Register an account, complete your profile, then explore universities, scholarships, AI advisor, and planner.

For a step-by-step walkthrough see [docs/STARTUP_GUIDE.md](docs/STARTUP_GUIDE.md).

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Yes | App secret for general signing |
| `JWT_SECRET` | Yes | JWT signing key (32+ chars) |
| `AUTH_SECRET` | Yes | NextAuth secret (must match frontend) |
| `OPENROUTER_API_KEY` | One of these | OpenRouter API key — preferred provider when set |
| `OPENROUTER_MODEL` | No | Default: `openai/gpt-4o-mini` |
| `GEMINI_API_KEY` | One of these | Google Gemini API key — used when OpenRouter is not configured |
| `GEMINI_MODEL` | No | Default: `gemini-2.5-flash` |
| `CORS_ORIGINS` | No | Allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL for frontend (in `.env.local`) |

Full template: [.env.example](.env.example)

---

## Security — what is NOT pushed to GitHub

The following are **gitignored** and must stay on your machine only:

| Ignored | Why |
|---------|-----|
| `.env`, `.env.local` | API keys, DB passwords, JWT secrets |
| `uploads/` | User-uploaded documents |
| `data/` | Local PostgreSQL data files |
| `tools/` | Local PostgreSQL binaries |
| `.venv/`, `node_modules/` | Dependencies |

**Never commit:**

- OpenRouter / Gemini API keys
- Database passwords or Neon connection strings
- JWT / NextAuth secrets
- Uploaded student documents

If a secret was ever exposed, rotate it immediately (OpenRouter dashboard / Google AI Studio) and regenerate your JWT/AUTH secrets.

---

## Database migrations

```bash
cd apps/api
alembic upgrade head
```

---

## Testing

**Backend**

```bash
cd apps/api
pytest
```

**Frontend lint**

```bash
npm run lint:web
```

---

## AI integration

Generative AI is selected by `get_generative_service()` in `apps/api/app/services/ai/__init__.py`:

1. **OpenRouter** (`openrouter_service.py`) when `OPENROUTER_API_KEY` is set
2. **Gemini** (`gemini_service.py`) when only `GEMINI_API_KEY` is set
3. Built-in fallback text when neither key is set

`/health/ai` reports `active_provider`, `openrouter_configured`, `gemini_configured`, and `llm_model`.

Supported methods: `generate_text()`, `chat()`, `rewrite()`, `summarize()`, `analyze()`.

---

## Deployment (production)

Recommended stack:

- **Database:** Neon PostgreSQL
- **Backend:** Any Python host (Railway, Render, Fly.io, VPS)
- **Frontend:** Vercel or similar
- Set `ENVIRONMENT=production`, strong secrets, and a valid `OPENROUTER_API_KEY` or `GEMINI_API_KEY`
- Use managed storage for uploads in production

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Keep changes focused — do not rewrite recommendation/scoring logic unless explicitly requested
4. Never commit `.env` files or API keys
5. Open a pull request with a clear description

---

## 👤 Author

**Md. Mahamudul Hasan**

- GitHub: [@mahamudul-hasan-cse](https://github.com/mahamudul-hasan-cse)

---


## Support

For setup issues, check [docs/STARTUP_GUIDE.md](docs/STARTUP_GUIDE.md) or open a GitHub issue.

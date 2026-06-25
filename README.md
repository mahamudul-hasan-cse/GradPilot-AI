# GradPilot AI

Production-grade SaaS platform helping students study abroad with university discovery, scholarship search, AI guidance, SOP assistance, and application tracking.

## Architecture

```
GradPilot-AI/
├── apps/
│   ├── api/          # FastAPI backend (clean architecture)
│   └── web/          # Next.js 15 frontend
├── packages/
│   └── shared/       # Shared TypeScript types
├── docker-compose.yml
├── .env.example
└── README.md
```

### Backend layers (`apps/api`)

| Layer | Responsibility |
|-------|----------------|
| `api/v1/endpoints` | HTTP routes, request/response mapping |
| `services` | Business logic |
| `repositories` | Data access (repository pattern) |
| `models` | SQLAlchemy ORM entities |
| `schemas` | Pydantic DTOs |
| `core` | Config, security, dependencies |

API versioning: all routes under `/api/v1`.

## Tech stack

- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT
- **AI (foundation):** LangChain, LangGraph, OpenAI, Qdrant
- **Infra:** Docker, Docker Compose

## Prerequisites

- Docker & Docker Compose
- Node.js 20+ (local frontend dev)
- Python 3.12+ (local backend dev)

## Quick start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY and OPENAI_API_KEY

# 2. Start all services
docker compose up --build

# 3. Access
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API docs:  http://localhost:8000/docs
# Qdrant:    http://localhost:6333
```

Migrations run automatically on API container startup.

### Seed sample data

```bash
docker compose exec api python scripts/seed_universities.py
```

See [University Discovery API](docs/UNIVERSITY_DISCOVERY.md) for filter, search, semantic search, and recommendation endpoints.

See [Scholarship Matching Engine](docs/SCHOLARSHIP_MATCHING_ENGINE.md) for eligibility scoring, match categories, and admin analytics.

See [Profile Intelligence Engine](docs/PROFILE_INTELLIGENCE.md) for admission readiness scoring, insights, and improvement recommendations.

See [AI Knowledge Platform](docs/AI_KNOWLEDGE_PLATFORM.md) for RAG architecture, hybrid search, citations, and conversation memory.

See [Application Workspace](docs/APPLICATION_WORKSPACE.md) for progress tracking, tasks, deadlines, and activity timeline.

See [Digital Twin & Orchestrator](docs/DIGITAL_TWIN.md) for unified student state, event bus, and AI orchestration.

See [Document Intelligence](docs/DOCUMENT_INTELLIGENCE.md) for OCR, extraction, validation, and twin sync.

## Local development (without Docker)

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL locally or use docker compose up postgres qdrant -d
export DATABASE_URL=postgresql+asyncpg://gradpilot:gradpilot_secret@localhost:5432/gradpilot
export DATABASE_URL_SYNC=postgresql+psycopg2://gradpilot:gradpilot_secret@localhost:5432/gradpilot
export JWT_SECRET_KEY=your-dev-secret

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
# From repo root (npm workspaces)
npm install
npm run dev:web
```

## Environment variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL connection (SQLAlchemy) |
| `DATABASE_URL_SYNC` | Sync URL for Alembic migrations |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `OPENAI_API_KEY` | OpenAI API key (AI features) |
| `QDRANT_HOST` | Qdrant vector DB host |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend |

## Database models

- **User** — authentication & roles
- **StudentProfile** — academic background, targets, budget
- **University** / **Program** — institution & degree catalog
- **Scholarship** — funding opportunities
- **Application** — application tracking
- **ChatSession** — AI conversation history (foundation)

## API endpoints (v1)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register user |
| POST | `/api/v1/auth/login` | No | Login, get JWT |
| POST | `/api/v1/auth/refresh` | No | Refresh tokens |
| GET | `/api/v1/auth/me` | Yes | Current user |
| GET/POST/PUT | `/api/v1/profile` | Yes | Student profile CRUD |
| POST | `/api/v1/profile/analyze` | No* | Profile intelligence — readiness scores & guidance |
| GET | `/api/v1/profile/analyze/analytics` | No | Admin analytics for profile intelligence |
| POST | `/api/v1/ai/search` | No* | Hybrid knowledge search (PG + Qdrant + BM25) |
| POST | `/api/v1/ai/chat` | Yes | RAG knowledge Q&A with citations + streaming |
| GET | `/api/v1/ai/conversations` | Yes | List knowledge conversation sessions |
| POST | `/api/v1/ai/index` | Yes | Re-index knowledge base |
| GET | `/api/v1/student/digital-twin` | Yes | Unified student digital twin state |
| GET | `/api/v1/student/timeline` | Yes | Chronological student journey |
| POST | `/api/v1/student/events` | Yes | Publish platform event |
| POST | `/api/v1/student/refresh` | Yes | Refresh all intelligence services |
| POST | `/api/v1/documents/upload` | Yes | Upload & parse admission documents |
| GET | `/api/v1/documents` | Yes | List documents with extractions |
| POST | `/api/v1/documents/{id}/parse` | Yes | Run OCR → extract → validate pipeline |
| GET | `/api/v1/documents/jobs/{id}` | Yes | Async processing job status |
| GET | `/api/v1/universities` | No | List universities |
| GET | `/api/v1/universities/filter` | No | Filter by tuition, GPA, country, major |
| POST | `/api/v1/universities/search` | No | Keyword search |
| POST | `/api/v1/universities/semantic-search` | No | Semantic search (Qdrant) |
| POST | `/api/v1/recommend-universities` | No | Safe / Target / Ambitious recommendations (legacy) |
| POST | `/api/v1/recommendations/universities` | No | Recommendation engine with explanations + Redis cache |
| POST | `/api/v1/recommendations/scholarships` | No | Scholarship matching engine with eligibility scoring |
| GET | `/api/v1/recommendations/scholarships/analytics` | No | Admin analytics for scholarship recommendations |
| GET | `/api/v1/universities/{id}` | No | University + programs |
| GET | `/api/v1/scholarships` | No | Search scholarships |
| GET | `/api/v1/scholarships/{id}` | No | Scholarship detail |
| GET/POST | `/api/v1/applications` | Yes | List/create application workspaces |
| GET | `/api/v1/applications/{id}/workspace` | Yes | Full workspace (progress, docs, tasks, timeline) |
| GET | `/api/v1/applications/{id}/progress` | Yes | Progress calculation (20/30/15/15/20) |
| GET/POST/PATCH/DELETE | `/api/v1/applications/{id}/documents` | Yes | Document management |
| GET/POST/PATCH/DELETE | `/api/v1/applications/{id}/tasks` | Yes | Task management |
| POST | `/api/v1/applications/{id}/tasks/generate` | Yes | Auto-generate intelligent tasks |
| GET/POST/PATCH/DELETE | `/api/v1/applications/{id}/notes` | Yes | Application notes |
| GET/POST/PATCH/DELETE | `/api/v1/applications/{id}/deadlines` | Yes | Deadline tracking + reminders |
| GET | `/api/v1/applications/{id}/timeline` | Yes | Activity timeline |
| GET | `/api/v1/applications/analytics` | Yes | Admin dashboard metrics |
| GET/PATCH/DELETE | `/api/v1/applications/{id}` | Yes | Application CRUD |

## API examples

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"securepass123","full_name":"Jane Doe"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"securepass123"}'
```

Response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Create student profile

```bash
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nationality": "India",
    "education_level": "Bachelors",
    "field_of_study": "Computer Science",
    "gpa": 3.8,
    "target_degree": "Masters",
    "target_countries": ["United States", "United Kingdom"]
  }'
```

### Search universities

```bash
curl "http://localhost:8000/api/v1/universities?country=United%20States&q=MIT&limit=10"
```

### Create application

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"university_id":"<uuid>","status":"in_progress","notes":"Gathering LORs"}'
```

## Migrations

```bash
# Create new migration
docker compose exec api alembic revision --autogenerate -m "describe change"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback one step
docker compose exec api alembic downgrade -1
```

## Testing

```bash
cd apps/api
pytest -v
```

## Development roadmap

### Phase 1 — Foundation (current)
- [x] Monorepo structure
- [x] Docker Compose dev environment
- [x] FastAPI with clean architecture
- [x] JWT authentication
- [x] Database models & Alembic migrations
- [x] REST APIs (auth, profile, universities, scholarships, applications)
- [x] Next.js frontend shell with Shadcn UI

### Phase 2 — Discovery
- [ ] University & scholarship data ingestion pipeline
- [ ] Qdrant embedding index for semantic search
- [ ] Admin APIs for catalog management
- [ ] Advanced search filters & ranking

### Phase 3 — AI Copilot
- [ ] LangGraph guidance workflows
- [ ] Chat session API & streaming responses
- [ ] SOP co-pilot with document upload
- [ ] Profile-aware recommendations

### Phase 4 — Production
- [ ] CI/CD (GitHub Actions)
- [ ] Observability (logging, metrics, tracing)
- [ ] Email verification & password reset
- [ ] Billing (Stripe) & team accounts
- [ ] Kubernetes / cloud deployment

## Makefile shortcuts

```bash
make up        # docker compose up -d
make down      # docker compose down
make migrate   # run alembic upgrade head
make logs      # tail all service logs
```

## License

Proprietary — GradPilot AI

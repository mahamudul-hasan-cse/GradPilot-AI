# Application Workspace

Central workspace where students manage each university application — documents, tasks, deadlines, notes, progress, and activity timeline.

## Data Model

```
User
  └── Application
        ├── University / Program / Scholarship
        ├── Documents (application_documents)
        ├── Tasks (application_tasks)
        ├── Deadlines (application_deadlines)
        ├── Notes (application_notes)
        └── Activity Timeline (application_activity)
```

## Application States

| State | Description |
|-------|-------------|
| `planning` | Initial setup |
| `preparing` | Gathering materials |
| `ready` | Ready to submit |
| `submitted` | Application submitted |
| `interview` | Interview stage |
| `accepted` | Offer received |
| `rejected` | Not admitted |
| `deferred` | Decision deferred |
| `withdrawn` | Student withdrew |

## Progress Engine

| Component | Weight |
|-----------|--------|
| Profile Complete | 20% |
| Documents | 30% |
| SOP | 15% |
| Recommendation Letter | 15% |
| Application Submitted | 20% |

Progress is auto-calculated from completion flags and uploaded documents.

## Auto-Generated Tasks

On application create:
- Upload official transcript
- Generate Statement of Purpose
- Request recommendation letters
- Pay application fee
- Submit application
- Prepare visa application

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/applications` | List applications |
| POST | `/applications` | Create workspace |
| GET | `/applications/{id}/workspace` | Full workspace view |
| GET | `/applications/{id}/progress` | Progress calculation |
| GET/POST/PATCH/DELETE | `/applications/{id}/documents` | Document management |
| GET/POST/PATCH/DELETE | `/applications/{id}/tasks` | Task management |
| POST | `/applications/{id}/tasks/generate` | Generate default tasks |
| GET/POST/PATCH/DELETE | `/applications/{id}/notes` | Notes |
| GET/POST/PATCH/DELETE | `/applications/{id}/deadlines` | Deadlines |
| GET | `/applications/{id}/timeline` | Activity timeline |
| GET | `/applications/analytics` | Admin dashboard |
| POST | `/applications/reminders/process` | Process deadline reminders |

## Setup

```bash
cd apps/api
alembic upgrade head
pytest tests/test_application_workspace.py -v
```

## Example

```bash
# Create application workspace
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "university_id": "uuid",
    "title": "MIT MS Computer Science",
    "intake_term": "Fall 2026",
    "deadline": "2026-01-15"
  }'

# Get full workspace with progress bar
curl http://localhost:8000/api/v1/applications/{id}/workspace \
  -H "Authorization: Bearer $TOKEN"
```

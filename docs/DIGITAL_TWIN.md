# Student Digital Twin & AI Orchestrator

Unified student state that all GradPilot intelligence services read from and update.

## Architecture

```
Student
  ↓
Digital Twin (single source of truth)
  ↓
AI Orchestrator
  ↓
Services
  • Profile Intelligence
  • University Recommendation
  • Scholarship Matching
  • Knowledge Platform
  • Application Workspace
  • Document Intelligence (future)
```

## Digital Twin State

| Section | Source |
|---------|--------|
| `academic_profile` | Student profile |
| `language_tests` | Profile test scores |
| `documents` | Application workspace documents |
| `applications` | Application workspace |
| `universities` | Applications + recommendations |
| `scholarships` | Scholarship matches |
| `recommendations` | Latest analysis + uni + scholarship recs |
| `deadlines` | Application deadlines |
| `preferences` | Target countries, budget |
| `goals` | Degree + country goals |
| `achievements` | Derived strengths |
| `weaknesses` | Profile analysis gaps |

## Event System

| Event | Triggers Refresh |
|-------|------------------|
| `profile.updated` | Yes |
| `document.uploaded` | Yes |
| `recommendation.generated` | No |
| `application.submitted` | Yes |
| `scholarship.added` | No |
| `deadline.passed` | No |
| `analysis.completed` | Yes |
| `twin.refreshed` | No |

Events are persisted to `twin_events`, cached in Redis (`twin:events:{user_id}`), and recorded in `twin_timeline`.

## Service Registry

All intelligence modules register capabilities at startup:

- `profile_intelligence` — analyze, score, recommend_actions
- `university_recommendation` — recommend, score, explain
- `scholarship_matching` — match, score, explain
- `knowledge_platform` — search, chat, cite
- `application_workspace` — track, tasks, deadlines, progress
- `document_intelligence` — future placeholder
- `digital_twin` — aggregate, orchestrate, refresh, timeline

## APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/student/digital-twin` | Full twin state + service registry |
| GET | `/api/v1/student/timeline` | Chronological journey |
| POST | `/api/v1/student/events` | Publish platform event |
| POST | `/api/v1/student/refresh` | Refresh all intelligence services |

## Refresh Flow

When profile changes (or manual refresh):

1. Profile Intelligence → new analysis
2. University Recommendation → updated matches
3. Scholarship Matching → updated matches
4. Digital Twin → re-aggregated state
5. Timeline → refresh event recorded

## Setup

```bash
cd apps/api
alembic upgrade head
pytest tests/test_digital_twin.py -v
```

## Example

```bash
# Get digital twin
curl http://localhost:8000/api/v1/student/digital-twin \
  -H "Authorization: Bearer $TOKEN"

# Publish profile update event (auto-refreshes recommendations)
curl -X POST http://localhost:8000/api/v1/student/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "profile.updated",
    "source_service": "profile",
    "payload": {"title": "Profile updated"}
  }'

# Manual full refresh
curl -X POST http://localhost:8000/api/v1/student/refresh \
  -H "Authorization: Bearer $TOKEN"
```

## Future AI Agents

The Digital Twin `state_snapshot` JSON is designed as the canonical context object for autonomous agents. Register new services via `ServiceRegistry.register()` and publish events via `POST /student/events`.

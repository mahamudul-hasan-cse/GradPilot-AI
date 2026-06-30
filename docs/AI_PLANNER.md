# AI Planner

Proactively generates personalized study-abroad action plans from the Student Digital Twin.

## Inputs

| Source | Data used |
|--------|-----------|
| Profile Analysis | Weaknesses, recommended actions, readiness scores |
| Recommendations | University and scholarship matches |
| Documents | Uploaded / missing document types |
| Deadlines | Application and intake deadlines |
| Timeline | Twin event history |
| Applications | Active workspaces and status |

## Outputs

| Output | Description |
|--------|-------------|
| Today's Tasks | High-priority actions scheduled for today |
| Tomorrow's Tasks | Next-day queue |
| Weekly Goals | 5 focus items with reasons |
| Monthly Roadmap | Phased plan (profile → shortlist → submit) |
| Missing Requirements | Gaps blocking readiness |
| Risk Alerts | Urgent risks (deadlines, profile gaps) |
| Deadline Alerts | Upcoming and missed deadlines |
| Priority Score | 0–100 composite plan urgency |
| Readiness Timeline | Estimated milestones to application-ready |

## Architecture

```
Digital Twin → PlannerRecommendationEngine → PriorityEngine → TimelineOptimizer
                    ↓                              ↓
              planner_tasks                  planner_schedule
              planner_notifications          planner_history (Redis cache)
```

## Components

| Component | Path |
|-----------|------|
| PlannerService | `services/ai_planner/service.py` |
| PriorityEngine | `services/ai_planner/priority_engine.py` |
| TimelineOptimizer | `services/ai_planner/timeline_optimizer.py` |
| PlannerRecommendationEngine | `services/ai_planner/recommendation_engine.py` |
| ReminderEngine | `services/ai_planner/reminder_engine.py` |

## APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/planner/generate` | Generate full plan |
| POST | `/api/v1/planner/regenerate` | Force regenerate |
| GET | `/api/v1/planner/plan` | Current plan |
| GET | `/api/v1/planner/tasks/today` | Today's tasks |
| GET | `/api/v1/planner/tasks/tomorrow` | Tomorrow's tasks |
| GET | `/api/v1/planner/weekly-goals` | Weekly goals |
| GET | `/api/v1/planner/calendar` | Calendar entries |
| GET | `/api/v1/planner/digest/daily` | Daily digest |
| GET | `/api/v1/planner/digest/weekly` | Weekly digest |
| GET | `/api/v1/planner/notifications` | Alerts & reminders |
| GET | `/api/v1/planner/analytics` | Admin analytics |

## Explainability

Every task, goal, alert, and schedule entry includes a `reason` field describing **why** it was generated from twin state.

## Auto-regeneration

When the Digital Twin changes (profile update, document upload, application change, analysis completed), the orchestrator automatically regenerates the plan via `PLANNER_REGENERATION_EVENTS`.

## Setup

```bash
cd apps/api
alembic upgrade head
pytest tests/test_ai_planner.py -v
```

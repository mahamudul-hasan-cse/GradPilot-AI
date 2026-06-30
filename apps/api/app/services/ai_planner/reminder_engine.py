"""Reminder and digest engine for planner notifications."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.models.ai_planner import PlannerNotification, PlannerTask
from app.services.ai_planner.types import PlannerNotificationDraft, PlannerTaskDraft


class ReminderEngine:
    def build_daily_digest(
        self,
        tasks: list[PlannerTask],
        notifications: list[PlannerNotification],
        *,
        today: date | None = None,
    ) -> dict:
        today = today or date.today()
        today_tasks = [t for t in tasks if t.scheduled_date == today or t.time_horizon == "today"]
        unread = [n for n in notifications if not n.is_read]

        highlights = [
            {
                "title": t.title,
                "reason": t.reason,
                "category": t.category,
                "priority_score": float(t.priority_score),
            }
            for t in today_tasks[:5]
        ]

        return {
            "digest_type": "daily",
            "title": f"Your plan for {today.isoformat()}",
            "summary": f"{len(today_tasks)} tasks today, {len(unread)} unread alerts.",
            "highlights": highlights,
            "tasks_due": today_tasks,
            "alerts": unread[:5],
            "generated_at": datetime.now(UTC),
        }

    def build_weekly_digest(
        self,
        tasks: list[PlannerTask],
        weekly_goals: list[dict],
    ) -> dict:
        week_tasks = [t for t in tasks if t.time_horizon in ("today", "tomorrow", "week")]
        return {
            "digest_type": "weekly",
            "title": "Weekly study-abroad plan",
            "summary": f"{len(week_tasks)} tasks scheduled this week across your applications.",
            "highlights": weekly_goals,
            "tasks_due": week_tasks[:10],
            "alerts": [],
            "generated_at": datetime.now(UTC),
        }

    def create_reminder_notifications(
        self,
        tasks: list[PlannerTaskDraft],
        *,
        today: date | None = None,
    ) -> list[PlannerNotificationDraft]:
        today = today or date.today()
        reminders = []
        for task in tasks:
            if task.due_date and (task.due_date - today).days in (1, 3, 7):
                days = (task.due_date - today).days
                reminders.append(PlannerNotificationDraft(
                    notification_type="reminder",
                    title=f"Reminder: {task.title}",
                    message=f"Due in {days} day(s) on {task.due_date.isoformat()}",
                    reason=task.reason,
                    severity="info",
                    scheduled_for=datetime.combine(today, datetime.min.time(), tzinfo=UTC),
                ))
        return reminders

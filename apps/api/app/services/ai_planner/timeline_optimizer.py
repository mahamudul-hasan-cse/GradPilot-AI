"""Timeline optimizer — schedule tasks and estimate readiness."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from app.services.ai_planner.types import PlannerScheduleDraft, PlannerTaskDraft
from app.services.digital_twin.types import TwinState

WORK_START_HOUR = 9
TASK_DURATION_HOURS = 1.5


class TimelineOptimizer:
    def assign_horizons(self, tasks: list[PlannerTaskDraft], *, today: date | None = None) -> list[PlannerTaskDraft]:
        today = today or date.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)

        for task in tasks:
            if task.due_date and task.due_date <= today:
                task.scheduled_date = today
                task.time_horizon = "today"
            elif task.due_date and task.due_date == tomorrow:
                task.scheduled_date = tomorrow
                task.time_horizon = "tomorrow"
            elif task.priority_score >= 0.7 and not task.scheduled_date:
                task.scheduled_date = today
                task.time_horizon = "today"
            elif task.priority_score >= 0.5 and not task.scheduled_date:
                task.scheduled_date = tomorrow
                task.time_horizon = "tomorrow"
            elif task.due_date and task.due_date <= week_end:
                task.scheduled_date = task.due_date
                task.time_horizon = "week"
            else:
                task.scheduled_date = today + timedelta(days=min(14, (task.due_date - today).days if task.due_date else 14))
                task.time_horizon = "month"
        return tasks

    def build_schedule(
        self,
        tasks: list[PlannerTaskDraft],
        *,
        today: date | None = None,
    ) -> list[PlannerScheduleDraft]:
        today = today or date.today()
        schedule: list[PlannerScheduleDraft] = []
        slot_hour = WORK_START_HOUR

        for idx, task in enumerate(tasks):
            if task.time_horizon not in ("today", "tomorrow"):
                continue
            sched_date = task.scheduled_date or today
            start = datetime.combine(sched_date, time(hour=slot_hour % 18, minute=0), tzinfo=UTC)
            end = start + timedelta(hours=TASK_DURATION_HOURS)
            schedule.append(
                PlannerScheduleDraft(
                    title=task.title,
                    description=task.description,
                    schedule_type="task",
                    reason=f"Scheduled because: {task.reason}",
                    start_at=start,
                    end_at=end,
                    task_index=idx,
                )
            )
            slot_hour += 2

        return schedule

    def estimate_readiness_timeline(
        self,
        twin: TwinState,
        tasks: list[PlannerTaskDraft],
        *,
        today: date | None = None,
    ) -> tuple[list[dict], dict[str, float]]:
        today = today or date.today()
        readiness = self._extract_readiness(twin)
        pending = len([t for t in tasks if t.category in ("document", "profile", "language_test")])
        weeks_to_complete = max(2, min(16, pending * 2))

        milestones = [
            {
                "label": "Profile complete",
                "target_date": (today + timedelta(weeks=1)).isoformat(),
                "readiness_percent": min(100, readiness + 15),
                "reason": "Complete profile fields to unlock accurate university matching.",
            },
            {
                "label": "Documents ready",
                "target_date": (today + timedelta(weeks=weeks_to_complete // 2)).isoformat(),
                "readiness_percent": min(100, readiness + 35),
                "reason": f"{pending} document-related tasks identified from your twin state.",
            },
            {
                "label": "Application-ready",
                "target_date": (today + timedelta(weeks=weeks_to_complete)).isoformat(),
                "readiness_percent": min(100, readiness + 55),
                "reason": "Estimated based on missing requirements and deadline pressure.",
            },
        ]

        prediction = {
            "current_readiness": readiness,
            "predicted_30_day": min(100.0, readiness + 20),
            "predicted_60_day": min(100.0, readiness + 40),
            "predicted_90_day": min(100.0, readiness + 60),
        }
        return milestones, prediction

    def _extract_readiness(self, twin: TwinState) -> float:
        analysis = twin.recommendations.get("profile_analysis") or {}
        if isinstance(analysis, dict):
            score = analysis.get("admission_readiness_score")
            if score is not None:
                return float(score)
        base = 30.0
        if twin.academic_profile.get("gpa"):
            base += 15
        if twin.language_tests.get("ielts") or twin.language_tests.get("toefl"):
            base += 15
        if twin.documents:
            base += min(20, len(twin.documents) * 5)
        return min(100.0, base)

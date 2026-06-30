"""Task prioritization engine."""

from __future__ import annotations

from datetime import date, timedelta

from app.services.ai_planner.types import PlannerTaskDraft
from app.services.digital_twin.types import TwinState

URGENCY_WEIGHT = 0.45
IMPORTANCE_WEIGHT = 0.35
GAP_WEIGHT = 0.20

CATEGORY_IMPORTANCE = {
    "deadline": 1.0,
    "document": 0.9,
    "language_test": 0.85,
    "profile": 0.8,
    "application": 0.85,
    "scholarship": 0.75,
    "recommendation": 0.7,
    "general": 0.5,
}


class PriorityEngine:
    def score_task(self, task: PlannerTaskDraft, *, today: date | None = None) -> float:
        today = today or date.today()
        importance = CATEGORY_IMPORTANCE.get(task.category, 0.5)

        urgency = 0.3
        if task.due_date:
            days_until = (task.due_date - today).days
            if days_until <= 0:
                urgency = 1.0
            elif days_until <= 3:
                urgency = 0.95
            elif days_until <= 7:
                urgency = 0.8
            elif days_until <= 14:
                urgency = 0.6
            elif days_until <= 30:
                urgency = 0.4
            else:
                urgency = 0.2

        gap_boost = 0.0
        if "missing" in task.reason.lower() or "gap" in task.reason.lower():
            gap_boost = 0.3
        elif "weakness" in task.reason.lower():
            gap_boost = 0.2

        score = (
            urgency * URGENCY_WEIGHT
            + importance * IMPORTANCE_WEIGHT
            + min(1.0, gap_boost + 0.1) * GAP_WEIGHT
        )
        return round(min(1.0, max(0.0, score)), 3)

    def rank_tasks(self, tasks: list[PlannerTaskDraft], *, today: date | None = None) -> list[PlannerTaskDraft]:
        today = today or date.today()
        for task in tasks:
            task.priority_score = self.score_task(task, today=today)
        ranked = sorted(tasks, key=lambda t: t.priority_score, reverse=True)
        return ranked

    def compute_plan_priority(self, tasks: list[PlannerTaskDraft]) -> float:
        if not tasks:
            return 0.0
        top_scores = [t.priority_score for t in tasks[:5]]
        return round(sum(top_scores) / len(top_scores) * 100, 2)

"""Tests for AI Planner."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.services.ai_planner.priority_engine import PriorityEngine
from app.services.ai_planner.recommendation_engine import PlannerRecommendationEngine
from app.services.ai_planner.reminder_engine import ReminderEngine
from app.services.ai_planner.timeline_optimizer import TimelineOptimizer
from app.services.ai_planner.types import PlannerTaskDraft
from app.services.digital_twin.types import PLANNER_REGENERATION_EVENTS, TwinEventType, TwinState
from app.services.recommendation.cache import RecommendationCache


def _twin(**kwargs) -> TwinState:
    defaults = {
        "user_id": uuid4(),
        "version": 1,
        "academic_profile": {},
        "language_tests": {},
        "documents": [],
        "applications": [],
        "universities": [],
        "scholarships": [],
        "recommendations": {},
        "deadlines": [],
        "preferences": {},
        "goals": [],
        "achievements": [],
        "weaknesses": [],
    }
    defaults.update(kwargs)
    return TwinState(**defaults)


class TestPriorityEngine:
    def test_urgent_deadline_scores_higher(self):
        engine = PriorityEngine()
        urgent = PlannerTaskDraft(
            title="Urgent",
            description=None,
            category="deadline",
            task_type="deadline",
            source="deadlines",
            reason="Due soon",
            due_date=date.today() + timedelta(days=2),
        )
        low = PlannerTaskDraft(
            title="Later",
            description=None,
            category="general",
            task_type="action",
            source="general",
            reason="Low priority",
            due_date=date.today() + timedelta(days=60),
        )
        assert engine.score_task(urgent) > engine.score_task(low)

    def test_rank_tasks_assigns_scores(self):
        engine = PriorityEngine()
        tasks = [
            PlannerTaskDraft("A", None, "general", "action", "g", "r"),
            PlannerTaskDraft("B", None, "deadline", "deadline", "d", "r", due_date=date.today()),
        ]
        ranked = engine.rank_tasks(tasks)
        assert ranked[0].priority_score >= ranked[1].priority_score


class TestRecommendationEngine:
    def test_generates_profile_tasks_with_reasons(self):
        engine = PlannerRecommendationEngine()
        twin = _twin(academic_profile={}, language_tests={})
        plan = engine.generate(twin)
        assert len(plan.tasks) > 0
        assert all(t.reason for t in plan.tasks)

    def test_detects_missing_documents(self):
        engine = PlannerRecommendationEngine()
        twin = _twin(documents=[])
        plan = engine.generate(twin)
        doc_tasks = [t for t in plan.tasks if t.category == "document"]
        assert len(doc_tasks) > 0
        assert any("passport" in t.title.lower() or "transcript" in t.title.lower() for t in doc_tasks)

    def test_missing_requirements_explained(self):
        engine = PlannerRecommendationEngine()
        twin = _twin(language_tests={}, documents=[], academic_profile={})
        plan = engine.generate(twin)
        assert len(plan.missing_requirements) > 0
        assert all("reason" in m for m in plan.missing_requirements)

    def test_risk_alerts_for_near_deadlines(self):
        engine = PlannerRecommendationEngine()
        tomorrow = (date.today() + timedelta(days=3)).isoformat()
        twin = _twin(deadlines=[{"title": "App deadline", "due_date": tomorrow}])
        plan = engine.generate(twin)
        assert len(plan.risk_alerts) > 0 or len(plan.deadline_alerts) > 0


class TestTimelineOptimizer:
    def test_assigns_today_horizon_for_high_priority(self):
        opt = TimelineOptimizer()
        task = PlannerTaskDraft(
            "High", None, "deadline", "deadline", "d", "r", priority_score=0.85,
            due_date=date.today(),
        )
        result = opt.assign_horizons([task])
        assert result[0].time_horizon == "today"

    def test_readiness_timeline_has_milestones(self):
        opt = TimelineOptimizer()
        twin = _twin(recommendations={"profile_analysis": {"admission_readiness_score": 45}})
        milestones, prediction = opt.estimate_readiness_timeline(twin, [])
        assert len(milestones) == 3
        assert "current_readiness" in prediction


class TestPlannerCache:
    def test_cache_key_deterministic(self):
        cache = RecommendationCache(prefix="planner:plans:")
        k1 = cache.build_cache_key({"user_id": "abc", "horizon": 30})
        k2 = cache.build_cache_key({"user_id": "abc", "horizon": 30})
        assert k1 == k2


class TestPlannerEvents:
    def test_planner_regeneration_events_include_profile_update(self):
        assert TwinEventType.PROFILE_UPDATED in PLANNER_REGENERATION_EVENTS
        assert TwinEventType.DOCUMENT_UPLOADED in PLANNER_REGENERATION_EVENTS

    def test_plan_generated_event_exists(self):
        assert TwinEventType.PLAN_GENERATED == "planner.generated"


class TestReminderEngine:
    def test_daily_digest_structure(self):
        engine = ReminderEngine()
        digest = engine.build_daily_digest([], [])
        assert digest["digest_type"] == "daily"
        assert "summary" in digest

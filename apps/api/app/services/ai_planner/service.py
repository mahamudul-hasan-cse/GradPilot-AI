"""AI Planner Service — proactive study-abroad action plans from Digital Twin."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_planner import PlannerHistory, PlannerNotification, PlannerSchedule, PlannerTask
from app.repositories.ai_planner import (
    PlannerHistoryRepository,
    PlannerNotificationRepository,
    PlannerScheduleRepository,
    PlannerTaskRepository,
)
from app.repositories.digital_twin import DigitalTwinRepository
from app.schemas.ai_planner import (
    ExplainedItem,
    PlannerAnalyticsResponse,
    PlannerCalendarResponse,
    PlannerDigestResponse,
    PlannerGenerateRequest,
    PlannerNotificationResponse,
    PlannerPlanResponse,
    PlannerScheduleResponse,
    PlannerTaskResponse,
    ReadinessMilestone,
)
from app.services.ai_planner.priority_engine import PriorityEngine
from app.services.ai_planner.recommendation_engine import PlannerRecommendationEngine
from app.services.ai_planner.reminder_engine import ReminderEngine
from app.services.ai_planner.timeline_optimizer import TimelineOptimizer
from app.services.digital_twin.aggregator import TwinAggregator
from app.services.digital_twin.orchestrator import AIOrchestrator
from app.services.digital_twin.types import TwinEventType
from app.services.recommendation.cache import RecommendationCache

logger = logging.getLogger(__name__)


class PlannerService:
    CACHE_PREFIX = "planner:plans:"

    def __init__(self, db: AsyncSession, cache: RecommendationCache | None = None):
        self.db = db
        self.history_repo = PlannerHistoryRepository(db)
        self.task_repo = PlannerTaskRepository(db)
        self.schedule_repo = PlannerScheduleRepository(db)
        self.notification_repo = PlannerNotificationRepository(db)
        self.twin_repo = DigitalTwinRepository(db)
        self.aggregator = TwinAggregator(db)
        self.cache = cache or RecommendationCache(prefix=self.CACHE_PREFIX)
        self.recommendation_engine = PlannerRecommendationEngine()
        self.priority_engine = PriorityEngine()
        self.timeline_optimizer = TimelineOptimizer()
        self.reminder_engine = ReminderEngine()

    async def generate_plan(
        self,
        user_id: UUID,
        request: PlannerGenerateRequest | None = None,
    ) -> PlannerPlanResponse:
        request = request or PlannerGenerateRequest()
        cache_key = self.cache.build_cache_key({"user_id": str(user_id), "horizon": request.horizon_days})

        if request.use_cache and not request.force_regenerate:
            cached = await self.cache.get(cache_key)
            if cached:
                response = PlannerPlanResponse.model_validate(cached)
                response.cache_hit = True
                return response

            latest = await self.history_repo.get_latest_for_user(user_id)
            twin = await self.twin_repo.get_by_user_id(user_id)
            if latest and twin and latest.twin_version >= twin.version:
                return await self._plan_from_history(latest, cache_hit=True)

        return await self._generate_and_persist(user_id, request, cache_key)

    async def regenerate(self, user_id: UUID, *, reason: str = "twin_changed") -> PlannerPlanResponse:
        request = PlannerGenerateRequest(use_cache=False, force_regenerate=True)
        cache_key = self.cache.build_cache_key({"user_id": str(user_id), "horizon": request.horizon_days})
        logger.info("Regenerating planner for user %s: %s", user_id, reason)
        return await self._generate_and_persist(user_id, request, cache_key, regeneration_reason=reason)

    async def _generate_and_persist(
        self,
        user_id: UUID,
        request: PlannerGenerateRequest,
        cache_key: str,
        *,
        regeneration_reason: str | None = None,
    ) -> PlannerPlanResponse:
        twin_state = await self.aggregator.build_state(user_id)
        existing_twin = await self.twin_repo.get_by_user_id(user_id)
        twin_version = existing_twin.version if existing_twin else 1

        draft = self.recommendation_engine.generate(twin_state)
        draft.tasks = self.priority_engine.rank_tasks(draft.tasks)
        draft.tasks = self.timeline_optimizer.assign_horizons(draft.tasks)
        draft.schedule = self.timeline_optimizer.build_schedule(draft.tasks)
        milestones, prediction = self.timeline_optimizer.estimate_readiness_timeline(twin_state, draft.tasks)
        draft.readiness_timeline = milestones
        draft.progress_prediction = prediction
        draft.priority_score = self.priority_engine.compute_plan_priority(draft.tasks)

        reminder_notifs = self.reminder_engine.create_reminder_notifications(draft.tasks)
        draft.notifications.extend(reminder_notifs)

        for rank, task in enumerate(draft.tasks, start=1):
            task.metadata = task.metadata or {}
            task.metadata["priority_rank"] = rank

        history = PlannerHistory(
            user_id=user_id,
            cache_key=cache_key,
            twin_version=twin_version,
            priority_score=draft.priority_score,
            readiness_timeline={"milestones": milestones, "prediction": prediction},
            request_payload=request.model_dump(mode="json"),
            response_summary={
                "task_count": len(draft.tasks),
                "regeneration_reason": regeneration_reason,
                "weekly_goals": draft.weekly_goals,
                "monthly_roadmap": draft.monthly_roadmap,
                "missing_requirements": draft.missing_requirements,
                "risk_alerts": draft.risk_alerts,
                "deadline_alerts": draft.deadline_alerts,
            },
            cache_hit=False,
        )
        history = await self.history_repo.create(history)

        saved_tasks = await self._persist_tasks(user_id, history.id, draft.tasks)
        await self._persist_schedule(user_id, history.id, draft.schedule, saved_tasks)
        await self._persist_notifications(user_id, history.id, draft.notifications)

        response = self._build_response(history, saved_tasks, draft)

        if request.use_cache:
            await self.cache.set(cache_key, response.model_dump(mode="json"))

        orchestrator = AIOrchestrator(self.db)
        await orchestrator.publish_event(
            user_id=user_id,
            event_type=TwinEventType.PLAN_GENERATED,
            source_service="ai_planner",
            payload={
                "title": "Study plan generated",
                "description": f"{len(saved_tasks)} tasks prioritized from your Digital Twin.",
                "plan_id": str(history.id),
                "priority_score": draft.priority_score,
            },
            auto_refresh=False,
        )

        return response

    async def _persist_tasks(
        self,
        user_id: UUID,
        plan_id: UUID,
        drafts: list,
    ) -> list[PlannerTask]:
        saved = []
        for rank, draft in enumerate(drafts, start=1):
            task = PlannerTask(
                user_id=user_id,
                plan_id=plan_id,
                title=draft.title,
                description=draft.description,
                category=draft.category,
                task_type=draft.task_type,
                source=draft.source,
                reason=draft.reason,
                priority_score=draft.priority_score,
                priority_rank=rank,
                scheduled_date=draft.scheduled_date,
                due_date=draft.due_date,
                time_horizon=draft.time_horizon,
                task_metadata=draft.metadata,
            )
            saved.append(await self.task_repo.create(task))
        return saved

    async def _persist_schedule(
        self,
        user_id: UUID,
        plan_id: UUID,
        drafts: list,
        tasks: list[PlannerTask],
    ) -> list[PlannerSchedule]:
        saved = []
        for draft in drafts:
            task_id = None
            if draft.task_index is not None and draft.task_index < len(tasks):
                task_id = tasks[draft.task_index].id
            entry = PlannerSchedule(
                user_id=user_id,
                plan_id=plan_id,
                task_id=task_id,
                title=draft.title,
                description=draft.description,
                schedule_type=draft.schedule_type,
                reason=draft.reason,
                start_at=draft.start_at,
                end_at=draft.end_at,
                schedule_metadata=draft.metadata,
            )
            saved.append(await self.schedule_repo.create(entry))
        return saved

    async def _persist_notifications(
        self,
        user_id: UUID,
        plan_id: UUID,
        drafts: list,
    ) -> list[PlannerNotification]:
        saved = []
        for draft in drafts:
            notif = PlannerNotification(
                user_id=user_id,
                plan_id=plan_id,
                notification_type=draft.notification_type,
                title=draft.title,
                message=draft.message,
                reason=draft.reason,
                severity=draft.severity,
                scheduled_for=draft.scheduled_for,
                sent_at=datetime.now(UTC),
                notification_metadata=draft.metadata,
            )
            saved.append(await self.notification_repo.create(notif))
        return saved

    def _build_response(
        self,
        history: PlannerHistory,
        tasks: list[PlannerTask],
        draft,
    ) -> PlannerPlanResponse:
        today_tasks = [t for t in tasks if t.time_horizon == "today"]
        tomorrow_tasks = [t for t in tasks if t.time_horizon == "tomorrow"]

        milestones_raw = draft.readiness_timeline or []
        milestones = [
            ReadinessMilestone(
                label=m["label"],
                target_date=date.fromisoformat(m["target_date"]) if isinstance(m["target_date"], str) else m["target_date"],
                readiness_percent=float(m["readiness_percent"]),
                reason=m["reason"],
            )
            for m in milestones_raw
        ]

        def to_explained(items: list[dict]) -> list[ExplainedItem]:
            return [
                ExplainedItem(
                    title=i.get("title", ""),
                    description=i.get("description"),
                    reason=i.get("reason", ""),
                    category=i.get("category"),
                    priority_score=i.get("priority_score"),
                )
                for i in items
            ]

        return PlannerPlanResponse(
            plan_id=history.id,
            priority_score=float(history.priority_score or draft.priority_score),
            cache_hit=history.cache_hit,
            twin_version=history.twin_version,
            todays_tasks=[PlannerTaskResponse.model_validate(t) for t in today_tasks],
            tomorrows_tasks=[PlannerTaskResponse.model_validate(t) for t in tomorrow_tasks],
            weekly_goals=to_explained(draft.weekly_goals),
            monthly_roadmap=to_explained(draft.monthly_roadmap),
            missing_requirements=to_explained(draft.missing_requirements),
            risk_alerts=to_explained(draft.risk_alerts),
            deadline_alerts=to_explained(draft.deadline_alerts),
            readiness_timeline=milestones,
            progress_prediction=draft.progress_prediction,
            generated_at=history.created_at,
        )

    async def _plan_from_history(self, history: PlannerHistory, *, cache_hit: bool) -> PlannerPlanResponse:
        tasks = await self.task_repo.get_by_plan(history.id)
        summary = history.response_summary or {}
        draft_data = history.readiness_timeline or {}

        class _Draft:
            weekly_goals = summary.get("weekly_goals", [])
            monthly_roadmap = summary.get("monthly_roadmap", [])
            missing_requirements = summary.get("missing_requirements", [])
            risk_alerts = summary.get("risk_alerts", [])
            deadline_alerts = summary.get("deadline_alerts", [])
            readiness_timeline = draft_data.get("milestones", [])
            progress_prediction = draft_data.get("prediction", {})
            priority_score = float(history.priority_score or 0)

        response = self._build_response(history, tasks, _Draft())
        response.cache_hit = cache_hit
        return response

    async def get_calendar(self, user_id: UUID, *, days: int = 14) -> PlannerCalendarResponse:
        start = datetime.now(UTC)
        end = start + timedelta(days=days)
        entries = await self.schedule_repo.get_by_user_range(user_id, start, end)
        return PlannerCalendarResponse(
            entries=[PlannerScheduleResponse.model_validate(e) for e in entries],
            start=start,
            end=end,
        )

    async def get_daily_digest(self, user_id: UUID) -> PlannerDigestResponse:
        latest = await self.history_repo.get_latest_for_user(user_id)
        if not latest:
            plan = await self.generate_plan(user_id)
            latest = await self.history_repo.get_latest_for_user(user_id)
        tasks = await self.task_repo.get_by_plan(latest.id) if latest else []
        notifications = await self.notification_repo.get_unread(user_id)
        digest = self.reminder_engine.build_daily_digest(tasks, notifications)
        return PlannerDigestResponse(
            digest_type=digest["digest_type"],
            title=digest["title"],
            summary=digest["summary"],
            highlights=[ExplainedItem(**h) for h in digest["highlights"]],
            tasks_due=[PlannerTaskResponse.model_validate(t) for t in digest["tasks_due"]],
            alerts=[PlannerNotificationResponse.model_validate(a) for a in digest["alerts"]],
            generated_at=digest["generated_at"],
        )

    async def get_weekly_digest(self, user_id: UUID) -> PlannerDigestResponse:
        latest = await self.history_repo.get_latest_for_user(user_id)
        if not latest:
            await self.generate_plan(user_id)
            latest = await self.history_repo.get_latest_for_user(user_id)
        tasks = await self.task_repo.get_by_plan(latest.id) if latest else []
        weekly_goals = (latest.response_summary or {}).get("weekly_goals", []) if latest else []
        digest = self.reminder_engine.build_weekly_digest(tasks, weekly_goals)
        return PlannerDigestResponse(
            digest_type=digest["digest_type"],
            title=digest["title"],
            summary=digest["summary"],
            highlights=[ExplainedItem(**h) for h in digest["highlights"]],
            tasks_due=[PlannerTaskResponse.model_validate(t) for t in digest["tasks_due"]],
            alerts=[],
            generated_at=digest["generated_at"],
        )

    async def get_analytics(self) -> PlannerAnalyticsResponse:
        from sqlalchemy import func, select

        total_plans = await self.history_repo.count_all()
        task_count = await self.db.execute(select(func.count()).select_from(PlannerTask))
        notif_count = await self.db.execute(select(func.count()).select_from(PlannerNotification))
        by_type = await self.notification_repo.count_by_type()

        avg_result = await self.db.execute(select(func.avg(PlannerHistory.priority_score)))
        avg_priority = float(avg_result.scalar_one() or 0)

        cache_hits = await self.db.execute(
            select(func.count()).select_from(PlannerHistory).where(PlannerHistory.cache_hit.is_(True))
        )
        hits = cache_hits.scalar_one() or 0
        hit_rate = (hits / total_plans * 100) if total_plans else 0.0

        cat_result = await self.db.execute(
            select(PlannerTask.category, func.count()).group_by(PlannerTask.category).limit(10)
        )
        top_categories = {row[0]: row[1] for row in cat_result.all()}

        return PlannerAnalyticsResponse(
            total_plans_generated=total_plans,
            total_tasks_created=task_count.scalar_one() or 0,
            total_notifications=notif_count.scalar_one() or 0,
            notifications_by_type=by_type,
            average_priority_score=round(avg_priority, 2),
            cache_hit_rate=round(hit_rate, 2),
            top_task_categories=top_categories,
        )

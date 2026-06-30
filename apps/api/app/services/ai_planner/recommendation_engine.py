"""Planner recommendation engine — generates tasks and goals from Digital Twin."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app.services.ai_planner.types import (
    PlannerNotificationDraft,
    PlannerPlanDraft,
    PlannerTaskDraft,
)
from app.services.digital_twin.types import TwinState

REQUIRED_DOCUMENTS = {"passport", "transcript", "cv", "ielts_trf", "sop", "lor"}


class PlannerRecommendationEngine:
    def generate(self, twin: TwinState) -> PlannerPlanDraft:
        tasks: list[PlannerTaskDraft] = []
        tasks.extend(self._profile_tasks(twin))
        tasks.extend(self._document_tasks(twin))
        tasks.extend(self._deadline_tasks(twin))
        tasks.extend(self._application_tasks(twin))
        tasks.extend(self._scholarship_tasks(twin))
        tasks.extend(self._analysis_tasks(twin))

        missing = self._missing_requirements(twin)
        risks = self._risk_alerts(twin)
        deadlines = self._deadline_alerts(twin)
        weekly = self._weekly_goals(twin, tasks)
        monthly = self._monthly_roadmap(twin, tasks)
        notifications = self._build_notifications(risks, deadlines)

        return PlannerPlanDraft(
            priority_score=0.0,
            tasks=tasks,
            schedule=[],
            notifications=notifications,
            weekly_goals=weekly,
            monthly_roadmap=monthly,
            missing_requirements=missing,
            risk_alerts=risks,
            deadline_alerts=deadlines,
            readiness_timeline=[],
            progress_prediction={},
        )

    def _profile_tasks(self, twin: TwinState) -> list[PlannerTaskDraft]:
        tasks = []
        academic = twin.academic_profile
        if not academic.get("target_degree"):
            tasks.append(PlannerTaskDraft(
                title="Set your target degree",
                description="Specify MSc, PhD, or other target degree in your profile.",
                category="profile",
                task_type="action",
                source="profile",
                reason="Target degree is missing — university matching cannot rank programs accurately without it.",
            ))
        if not academic.get("field_of_study"):
            tasks.append(PlannerTaskDraft(
                title="Add field of study",
                description="Enter your intended field of study.",
                category="profile",
                task_type="action",
                source="profile",
                reason="Field of study gap detected in Digital Twin academic profile.",
            ))
        if not twin.language_tests.get("ielts") and not twin.language_tests.get("toefl"):
            tasks.append(PlannerTaskDraft(
                title="Register for IELTS or TOEFL",
                description="Book a language test — required for most international programs.",
                category="language_test",
                task_type="action",
                source="profile",
                reason="No language test scores in your twin — this is a critical admission requirement.",
                due_date=date.today() + timedelta(days=30),
            ))
        return tasks

    def _document_tasks(self, twin: TwinState) -> list[PlannerTaskDraft]:
        tasks = []
        uploaded_types = {
            (d.get("classified_type") or d.get("document_type") or "").lower()
            for d in twin.documents
        }
        for doc_type in REQUIRED_DOCUMENTS - uploaded_types:
            label = doc_type.replace("_", " ").title()
            tasks.append(PlannerTaskDraft(
                title=f"Upload {label}",
                description=f"Upload and validate your {label} for document intelligence extraction.",
                category="document",
                task_type="upload",
                source="documents",
                reason=f"{label} not found in uploaded documents — required for complete application packages.",
                due_date=date.today() + timedelta(days=21),
            ))
        return tasks

    def _deadline_tasks(self, twin: TwinState) -> list[PlannerTaskDraft]:
        tasks = []
        today = date.today()
        for dl in twin.deadlines:
            due_str = dl.get("due_date") or dl.get("deadline")
            if not due_str:
                continue
            try:
                due = datetime.fromisoformat(str(due_str).replace("Z", "+00:00")).date()
            except ValueError:
                continue
            if due < today:
                continue
            days_left = (due - today).days
            tasks.append(PlannerTaskDraft(
                title=f"Prepare for: {dl.get('title', 'Application deadline')}",
                description=dl.get("description"),
                category="deadline",
                task_type="deadline",
                source="deadlines",
                reason=f"Deadline in {days_left} days — prioritized because late submissions reduce admission chances.",
                due_date=due,
            ))
        return tasks

    def _application_tasks(self, twin: TwinState) -> list[PlannerTaskDraft]:
        tasks = []
        for app in twin.applications:
            status = app.get("status", "")
            if status in ("submitted", "accepted", "rejected", "withdrawn"):
                continue
            tasks.append(PlannerTaskDraft(
                title=f"Advance application: {app.get('notes') or app.get('id', 'Application')[:8]}",
                description="Review tasks, documents, and progress in application workspace.",
                category="application",
                task_type="review",
                source="applications",
                reason=f"Application status is '{status}' — active applications need regular progress updates.",
            ))
        if not twin.applications:
            tasks.append(PlannerTaskDraft(
                title="Create your first application workspace",
                description="Start tracking a university application with tasks and deadlines.",
                category="application",
                task_type="action",
                source="applications",
                reason="No applications in Digital Twin — creating a workspace enables deadline and progress tracking.",
            ))
        return tasks

    def _scholarship_tasks(self, twin: TwinState) -> list[PlannerTaskDraft]:
        tasks = []
        sch_recs = twin.recommendations.get("scholarships") or []
        if sch_recs and isinstance(sch_recs, list):
            top = sch_recs[0] if sch_recs else None
            if top and isinstance(top, dict):
                tasks.append(PlannerTaskDraft(
                    title=f"Review scholarship: {top.get('title', 'Top match')[:60]}",
                    description="Check eligibility and prepare scholarship application materials.",
                    category="scholarship",
                    task_type="review",
                    source="scholarships",
                    reason="High-match scholarship found in recommendations — applying early improves funding odds.",
                ))
        elif not twin.scholarships:
            tasks.append(PlannerTaskDraft(
                title="Run scholarship matching",
                description="Generate personalized scholarship recommendations from your profile.",
                category="scholarship",
                task_type="action",
                source="scholarships",
                reason="No scholarship matches in twin — profile may be incomplete or matching not yet run.",
            ))
        return tasks

    def _analysis_tasks(self, twin: TwinState) -> list[PlannerTaskDraft]:
        tasks = []
        for weakness in twin.weaknesses[:3]:
            w = weakness if isinstance(weakness, str) else str(weakness)
            tasks.append(PlannerTaskDraft(
                title=f"Address: {w[:80]}",
                description="Follow profile intelligence recommendation to close this gap.",
                category="recommendation",
                task_type="improvement",
                source="profile_analysis",
                reason=f"Profile analysis identified weakness: {w}",
            ))
        analysis = twin.recommendations.get("profile_analysis") or {}
        actions = analysis.get("recommended_actions", []) if isinstance(analysis, dict) else []
        for action in actions[:2]:
            a = action if isinstance(action, str) else str(action)
            tasks.append(PlannerTaskDraft(
                title=a[:100],
                description=None,
                category="recommendation",
                task_type="action",
                source="profile_analysis",
                reason=f"Recommended by profile intelligence engine based on your readiness scores.",
            ))
        return tasks

    def _missing_requirements(self, twin: TwinState) -> list[dict]:
        items = []
        if not twin.language_tests.get("ielts") and not twin.language_tests.get("toefl"):
            items.append({
                "title": "Language test score",
                "reason": "IELTS/TOEFL not recorded in Digital Twin — required by most universities.",
                "category": "language_test",
            })
        uploaded = {(d.get("classified_type") or "").lower() for d in twin.documents}
        for doc in REQUIRED_DOCUMENTS - uploaded:
            items.append({
                "title": doc.replace("_", " ").title(),
                "reason": f"Document type '{doc}' missing from uploads.",
                "category": "document",
            })
        if not twin.academic_profile.get("gpa"):
            items.append({
                "title": "GPA / academic score",
                "reason": "GPA not set — affects university tier matching and readiness score.",
                "category": "profile",
            })
        return items

    def _risk_alerts(self, twin: TwinState) -> list[dict]:
        alerts = []
        today = date.today()
        for dl in twin.deadlines:
            due_str = dl.get("due_date") or dl.get("deadline")
            if not due_str:
                continue
            try:
                due = datetime.fromisoformat(str(due_str).replace("Z", "+00:00")).date()
            except ValueError:
                continue
            days = (due - today).days
            if 0 <= days <= 7:
                alerts.append({
                    "title": f"Urgent deadline: {dl.get('title', 'Application')}",
                    "reason": f"Only {days} days remaining — incomplete documents or tasks increase rejection risk.",
                    "category": "deadline",
                    "priority_score": 0.95,
                })
        if len(twin.weaknesses) >= 3:
            alerts.append({
                "title": "Multiple profile gaps detected",
                "reason": f"{len(twin.weaknesses)} weaknesses in profile analysis — readiness score may be below competitive thresholds.",
                "category": "profile",
                "priority_score": 0.8,
            })
        return alerts

    def _deadline_alerts(self, twin: TwinState) -> list[dict]:
        alerts = []
        today = date.today()
        for dl in twin.deadlines:
            due_str = dl.get("due_date") or dl.get("deadline")
            if not due_str:
                continue
            try:
                due = datetime.fromisoformat(str(due_str).replace("Z", "+00:00")).date()
            except ValueError:
                continue
            days = (due - today).days
            if days < 0:
                alerts.append({
                    "title": f"Missed: {dl.get('title', 'Deadline')}",
                    "reason": f"Deadline passed {abs(days)} days ago — review if extension or alternate intake is possible.",
                    "category": "deadline",
                })
            elif days <= 14:
                alerts.append({
                    "title": f"Upcoming: {dl.get('title', 'Deadline')}",
                    "reason": f"Due in {days} days on {due.isoformat()}.",
                    "category": "deadline",
                })
        return alerts

    def _weekly_goals(self, twin: TwinState, tasks: list[PlannerTaskDraft]) -> list[dict]:
        week_tasks = [t for t in tasks if t.time_horizon in ("today", "tomorrow", "week")][:5]
        goals = [
            {
                "title": t.title,
                "description": t.description,
                "reason": t.reason,
                "category": t.category,
            }
            for t in week_tasks
        ]
        if not goals:
            goals.append({
                "title": "Complete profile and upload core documents",
                "reason": "No urgent tasks — focus on foundation items to improve recommendation quality.",
                "category": "general",
            })
        return goals

    def _monthly_roadmap(self, twin: TwinState, tasks: list[PlannerTaskDraft]) -> list[dict]:
        phases = [
            {"title": "Week 1–2: Profile & documents", "reason": "Establish complete Digital Twin for accurate AI recommendations.", "category": "foundation"},
            {"title": "Week 3: University shortlist", "reason": "Run university matching and finalize 5–8 target programs.", "category": "discovery"},
            {"title": "Week 4: Applications & scholarships", "reason": "Submit applications and scholarship materials before deadlines.", "category": "submission"},
        ]
        if twin.applications:
            phases.append({
                "title": "Ongoing: Application workspace progress",
                "reason": f"{len(twin.applications)} active application(s) require weekly task completion.",
                "category": "application",
            })
        return phases

    def _build_notifications(
        self,
        risks: list[dict],
        deadlines: list[dict],
    ) -> list[PlannerNotificationDraft]:
        notifications = []
        for risk in risks:
            notifications.append(PlannerNotificationDraft(
                notification_type="risk_alert",
                title=risk["title"],
                message=risk["title"],
                reason=risk["reason"],
                severity="warning" if risk.get("priority_score", 0) < 0.9 else "critical",
            ))
        for dl in deadlines[:5]:
            notifications.append(PlannerNotificationDraft(
                notification_type="deadline_alert",
                title=dl["title"],
                message=dl["title"],
                reason=dl["reason"],
                severity="warning",
            ))
        return notifications

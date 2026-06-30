"""Aggregate student state from all platform services."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.document_intelligence import DocumentUpload
from app.models.profile_analysis import ProfileAnalysis
from app.models.recommendation import RecommendationHistory
from app.models.scholarship_recommendation import ScholarshipRecommendationHistory
from app.models.student_profile import StudentProfile
from app.repositories.student_profile import StudentProfileRepository
from app.services.digital_twin.types import TwinState


class TwinAggregator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = StudentProfileRepository(db)

    async def build_state(self, user_id: UUID, *, version: int = 1) -> TwinState:
        profile = await self.profile_repo.get_by_user_id(user_id)
        applications = await self._load_applications(user_id)
        profile_analysis = await self._latest_profile_analysis(user_id)
        uni_rec = await self._latest_university_recommendations(user_id)
        sch_rec = await self._latest_scholarship_recommendations(user_id)

        academic = self._build_academic_profile(profile)
        language = self._build_language_tests(profile)
        documents = self._collect_documents(applications)
        documents.extend(await self._collect_intelligence_documents(user_id))
        deadlines = self._collect_deadlines(applications)
        preferences = self._build_preferences(profile)
        achievements = self._build_achievements(profile, profile_analysis)
        weaknesses: list = []
        if profile_analysis and profile_analysis.response_summary:
            weaknesses = profile_analysis.response_summary.get("weaknesses", [])

        recommendations = {
            "profile_analysis": self._serialize_profile_analysis(profile_analysis),
            "universities": uni_rec,
            "scholarships": sch_rec,
            "study_plan": await self._latest_study_plan(user_id),
        }

        universities = self._extract_universities(applications, uni_rec)
        scholarships = self._extract_scholarships(applications, sch_rec)

        return TwinState(
            user_id=user_id,
            version=version,
            academic_profile=academic,
            language_tests=language,
            documents=documents,
            applications=[self._serialize_application(a) for a in applications],
            universities=universities,
            scholarships=scholarships,
            recommendations=recommendations,
            deadlines=deadlines,
            preferences=preferences,
            goals=self._build_goals(profile),
            achievements=achievements,
            weaknesses=weaknesses if isinstance(weaknesses, list) else [],
            last_synced_at=datetime.now(UTC).isoformat(),
        )

    async def _load_applications(self, user_id: UUID) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .options(
                selectinload(Application.university),
                selectinload(Application.documents),
                selectinload(Application.deadlines),
            )
            .where(Application.user_id == user_id)
            .order_by(Application.updated_at.desc())
        )
        return list(result.scalars().all())

    async def _latest_profile_analysis(self, user_id: UUID) -> ProfileAnalysis | None:
        result = await self.db.execute(
            select(ProfileAnalysis)
            .where(ProfileAnalysis.user_id == user_id)
            .order_by(ProfileAnalysis.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _latest_university_recommendations(self, user_id: UUID) -> dict | None:
        result = await self.db.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
            .limit(1)
        )
        rec = result.scalar_one_or_none()
        if not rec:
            return None
        return rec.response_summary

    async def _latest_scholarship_recommendations(self, user_id: UUID) -> dict | None:
        result = await self.db.execute(
            select(ScholarshipRecommendationHistory)
            .where(ScholarshipRecommendationHistory.user_id == user_id)
            .order_by(ScholarshipRecommendationHistory.created_at.desc())
            .limit(1)
        )
        rec = result.scalar_one_or_none()
        if not rec:
            return None
        return rec.response_summary

    def _build_academic_profile(self, profile: StudentProfile | None) -> dict:
        if not profile:
            return {"complete": False}
        gpa = float(profile.gpa) if profile.gpa else None
        scale = float(profile.gpa_scale or 4.0)
        cgpa = round(gpa * 4.0 / scale, 2) if gpa and scale else None
        return {
            "complete": True,
            "gpa": gpa,
            "gpa_scale": scale,
            "cgpa_normalized": cgpa,
            "education_level": profile.education_level,
            "field_of_study": profile.field_of_study,
            "target_degree": profile.target_degree,
            "nationality": profile.nationality,
            "work_experience_years": profile.work_experience_years,
        }

    def _build_language_tests(self, profile: StudentProfile | None) -> dict:
        if not profile or not profile.test_scores:
            return {}
        scores = profile.test_scores or {}
        return {
            "ielts": scores.get("ielts"),
            "toefl": scores.get("toefl"),
            "gre": scores.get("gre"),
            "gmat": scores.get("gmat"),
        }

    def _build_preferences(self, profile: StudentProfile | None) -> dict:
        if not profile:
            return {}
        return {
            "target_countries": profile.target_countries or [],
            "budget_min": float(profile.budget_min) if profile.budget_min else None,
            "budget_max": float(profile.budget_max) if profile.budget_max else None,
            "budget_currency": profile.budget_currency,
            "current_country": profile.current_country,
        }

    def _build_goals(self, profile: StudentProfile | None) -> list[dict]:
        if not profile:
            return []
        goals = []
        if profile.target_degree:
            goals.append({"type": "degree", "value": profile.target_degree})
        for country in profile.target_countries or []:
            goals.append({"type": "country", "value": country})
        return goals

    def _build_achievements(self, profile: StudentProfile | None, analysis: ProfileAnalysis | None) -> list[dict]:
        achievements = []
        if profile and profile.work_experience_years and profile.work_experience_years > 0:
            achievements.append({
                "type": "work_experience",
                "label": f"{profile.work_experience_years} years professional experience",
            })
        if analysis:
            score = float(analysis.admission_readiness_score or 0)
            if score >= 75:
                achievements.append({"type": "readiness", "label": f"Admission readiness {score:.0f}/100"})
        return achievements

    def _collect_documents(self, applications: list[Application]) -> list[dict]:
        docs = []
        for app in applications:
            for doc in app.documents or []:
                docs.append({
                    "id": str(doc.id),
                    "application_id": str(app.id),
                    "type": doc.document_type,
                    "title": doc.title,
                    "status": doc.status,
                })
        return docs

    async def _collect_intelligence_documents(self, user_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(DocumentUpload)
            .where(DocumentUpload.user_id == user_id)
            .order_by(DocumentUpload.created_at.desc())
            .limit(50)
        )
        return [
            {
                "id": str(d.id),
                "source": "document_intelligence",
                "type": d.classified_type or d.document_type,
                "file_name": d.file_name,
                "status": d.status,
                "confidence_score": float(d.confidence_score or 0),
                "extracted_fields": d.extracted_fields,
                "version": d.version,
            }
            for d in result.scalars().all()
        ]

    def _collect_deadlines(self, applications: list[Application]) -> list[dict]:
        items = []
        for app in applications:
            for dl in app.deadlines or []:
                items.append({
                    "id": str(dl.id),
                    "application_id": str(app.id),
                    "type": dl.deadline_type,
                    "title": dl.title,
                    "due_date": dl.due_date.isoformat(),
                    "is_completed": dl.is_completed,
                })
            if app.deadline:
                items.append({
                    "application_id": str(app.id),
                    "type": "application",
                    "title": app.title or "Application deadline",
                    "due_date": app.deadline.isoformat(),
                    "is_completed": app.status in {"submitted", "accepted", "rejected"},
                })
        return items

    def _serialize_application(self, app: Application) -> dict:
        return {
            "id": str(app.id),
            "title": app.title,
            "status": app.status,
            "progress_percent": float(app.progress_percent or 0),
            "university": app.university.name if app.university else None,
            "intake_term": app.intake_term,
            "deadline": app.deadline.isoformat() if app.deadline else None,
        }

    def _serialize_profile_analysis(self, analysis: ProfileAnalysis | None) -> dict | None:
        if not analysis:
            return None
        return {
            "admission_readiness_score": float(analysis.admission_readiness_score or 0),
            "scholarship_readiness_score": float(analysis.scholarship_readiness_score or 0),
            "employability_score": float(analysis.employability_score or 0),
            "tier": analysis.recommended_university_tier,
            "analyzed_at": analysis.created_at.isoformat(),
        }

    def _extract_universities(self, applications: list[Application], uni_rec: dict | None) -> list[dict]:
        unis = []
        seen = set()
        for app in applications:
            if app.university and app.university.id not in seen:
                seen.add(app.university.id)
                unis.append({
                    "id": str(app.university.id),
                    "name": app.university.name,
                    "country": app.university.country,
                    "source": "application",
                })
        if uni_rec:
            unis.append({"source": "recommendation", "summary": uni_rec})
        return unis

    def _extract_scholarships(self, applications: list[Application], sch_rec: dict | None) -> list[dict]:
        items = []
        if sch_rec:
            items.append({"source": "recommendation", "summary": sch_rec})
        return items

    async def _latest_study_plan(self, user_id: UUID) -> dict | None:
        from app.repositories.ai_planner import PlannerHistoryRepository

        history = await PlannerHistoryRepository(self.db).get_latest_for_user(user_id)
        if not history:
            return None
        return {
            "plan_id": str(history.id),
            "priority_score": float(history.priority_score) if history.priority_score else None,
            "twin_version": history.twin_version,
            "generated_at": history.created_at.isoformat() if history.created_at else None,
        }

    def profile_to_analysis_request(self, profile: StudentProfile) -> dict:
        gpa = float(profile.gpa or 3.0)
        scale = float(profile.gpa_scale or 4.0)
        cgpa = Decimal(str(round(gpa * 4.0 / scale, 2)))
        scores = profile.test_scores or {}
        ielts = Decimal(str(scores.get("ielts", 6.5)))
        return {
            "cgpa": cgpa,
            "ielts": ielts,
            "degree_level": profile.target_degree or "masters",
            "major": profile.field_of_study or "General",
            "country_preferences": profile.target_countries or [],
            "work_experience_years": profile.work_experience_years or 0,
            "nationality": profile.nationality,
            "use_cache": False,
        }

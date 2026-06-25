"""Human-readable explanations for scholarship matches."""

from __future__ import annotations

from app.models.scholarship import Scholarship
from app.services.scholarship_recommendation.scoring import (
    ScholarshipScoreBreakdown,
    ScholarshipStudentProfile,
)


class ScholarshipExplanationEngine:
    CATEGORY_LABELS = {
        "excellent": "Excellent Match",
        "strong": "Strong Match",
        "possible": "Possible Match",
        "low": "Low Match",
    }

    def explain(
        self,
        scholarship: Scholarship,
        profile: ScholarshipStudentProfile,
        breakdown: ScholarshipScoreBreakdown,
    ) -> str:
        parts: list[str] = []
        parts.extend(self._academic(scholarship, profile, breakdown))
        parts.extend(self._language(scholarship, profile))
        parts.extend(self._degree(scholarship, profile, breakdown))
        parts.extend(self._country(scholarship, profile, breakdown))
        parts.extend(self._research(scholarship, profile))
        parts.extend(self._work(scholarship, profile))
        parts.extend(self._nationality(scholarship, profile))
        parts.append(self._summary(breakdown))
        return " ".join(p for p in parts if p)

    def _academic(
        self,
        scholarship: Scholarship,
        profile: ScholarshipStudentProfile,
        breakdown: ScholarshipScoreBreakdown,
    ) -> list[str]:
        if scholarship.minimum_gpa is None:
            return ["No minimum GPA specified."]
        if profile.cgpa >= scholarship.minimum_gpa:
            return [f"You meet the GPA requirement ({scholarship.minimum_gpa})."]
        return [f"Your CGPA ({profile.cgpa}) is below the required {scholarship.minimum_gpa}."]

    def _language(self, scholarship: Scholarship, profile: ScholarshipStudentProfile) -> list[str]:
        if scholarship.minimum_ielts is None:
            return []
        if profile.ielts >= scholarship.minimum_ielts:
            return ["You meet IELTS requirements."]
        return [f"Your IELTS ({profile.ielts}) is below the required {scholarship.minimum_ielts}."]

    def _degree(
        self,
        scholarship: Scholarship,
        profile: ScholarshipStudentProfile,
        breakdown: ScholarshipScoreBreakdown,
    ) -> list[str]:
        if scholarship.degree_level and breakdown.degree_match >= 0.9:
            return [f"Your {profile.degree_level} degree level aligns with this scholarship."]
        if scholarship.degree_level:
            return [f"Degree level may not fully align (scholarship targets {scholarship.degree_level})."]
        return []

    def _country(
        self,
        scholarship: Scholarship,
        profile: ScholarshipStudentProfile,
        breakdown: ScholarshipScoreBreakdown,
    ) -> list[str]:
        if breakdown.country_match >= 0.9 and scholarship.country:
            return [f"Country preference matches ({scholarship.country})."]
        if scholarship.country and profile.country_preference:
            return [f"Scholarship is for {scholarship.country}; your preference is {profile.country_preference}."]
        return []

    def _research(self, scholarship: Scholarship, profile: ScholarshipStudentProfile) -> list[str]:
        if scholarship.research_required:
            if profile.has_research_experience:
                return ["Research experience requirement satisfied."]
            return ["Research experience is required but not indicated in your profile."]
        return []

    def _work(self, scholarship: Scholarship, profile: ScholarshipStudentProfile) -> list[str]:
        required = scholarship.work_experience_required_years
        if required and required > 0:
            if profile.work_experience_years >= required:
                return [f"Work experience requirement met ({required}+ years)."]
            return [f"Requires {required} years of work experience; you have {profile.work_experience_years}."]
        return []

    def _nationality(self, scholarship: Scholarship, profile: ScholarshipStudentProfile) -> list[str]:
        if scholarship.eligible_nationalities and profile.nationality:
            eligible = ", ".join(scholarship.eligible_nationalities[:5])
            if profile.nationality.lower() in [n.lower() for n in scholarship.eligible_nationalities]:
                return [f"Your nationality ({profile.nationality}) is eligible."]
            return [f"Nationality restrictions may apply (eligible: {eligible})."]
        return []

    def _summary(self, breakdown: ScholarshipScoreBreakdown) -> str:
        label = self.CATEGORY_LABELS.get(breakdown.match_category, breakdown.match_category)
        prob_pct = round(breakdown.eligibility_probability * 100, 1)
        return (
            f"{label} (score: {breakdown.scholarship_score:.0f}/100, "
            f"eligibility probability: {prob_pct}%)."
        )

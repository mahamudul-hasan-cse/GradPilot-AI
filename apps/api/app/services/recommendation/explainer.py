"""Human-readable explanations for university recommendations."""

from __future__ import annotations

from app.models.university import University
from app.services.recommendation.scoring import ScoreBreakdown, StudentRecommendationProfile


class RecommendationExplainer:
    def explain(
        self,
        university: University,
        profile: StudentRecommendationProfile,
        breakdown: ScoreBreakdown,
    ) -> str:
        parts: list[str] = []

        parts.extend(self._explain_academic(university, profile, breakdown))
        parts.extend(self._explain_language(university, profile, breakdown))
        parts.extend(self._explain_budget(university, profile, breakdown))
        parts.extend(self._explain_program(profile, breakdown))
        parts.extend(self._explain_scholarship(university, breakdown))
        parts.append(self._explain_tier(breakdown))

        return " ".join(parts)

    def _explain_academic(
        self,
        university: University,
        profile: StudentRecommendationProfile,
        breakdown: ScoreBreakdown,
    ) -> list[str]:
        sentences: list[str] = []
        if university.minimum_gpa is not None:
            if profile.cgpa >= university.minimum_gpa:
                sentences.append("You meet GPA requirements.")
            else:
                sentences.append(
                    f"Your GPA ({profile.cgpa}) is below the minimum ({university.minimum_gpa})."
                )
        else:
            sentences.append("GPA requirements are not specified for this university.")

        if profile.work_experience_years >= 1:
            sentences.append(
                f"Your {profile.work_experience_years} year(s) of work experience strengthens your profile."
            )
        if profile.has_research_experience:
            sentences.append("Your research experience is a positive factor for this program.")

        if breakdown.academic_match >= 0.8:
            sentences.append("Strong academic match.")
        return sentences

    def _explain_language(
        self,
        university: University,
        profile: StudentRecommendationProfile,
        breakdown: ScoreBreakdown,
    ) -> list[str]:
        if university.minimum_ielts is None:
            return ["IELTS requirements are not specified."]
        if profile.ielts >= university.minimum_ielts:
            return ["You meet IELTS requirements."]
        return [
            f"Your IELTS ({profile.ielts}) is below the minimum ({university.minimum_ielts})."
        ]

    def _explain_budget(
        self,
        university: University,
        profile: StudentRecommendationProfile,
        breakdown: ScoreBreakdown,
    ) -> list[str]:
        if university.tuition_fee is None:
            return ["Tuition information is not available."]
        if profile.budget >= university.tuition_fee:
            return ["Tuition is within budget."]
        return [
            f"Tuition (${university.tuition_fee:,.0f}) exceeds your budget (${profile.budget:,.0f})."
        ]

    def _explain_program(
        self,
        profile: StudentRecommendationProfile,
        breakdown: ScoreBreakdown,
    ) -> list[str]:
        if breakdown.program_match >= 0.85:
            return [f"Strong program match for {profile.major}."]
        if breakdown.program_match >= 0.55:
            return [f"Moderate program match for {profile.major}."]
        return [f"Limited program match for {profile.major}."]

    def _explain_scholarship(self, university: University, breakdown: ScoreBreakdown) -> list[str]:
        if university.scholarships_available:
            return ["Scholarship opportunities available."]
        return ["No scholarships currently listed for this university."]

    def _explain_tier(self, breakdown: ScoreBreakdown) -> str:
        tier_messages = {
            "safe": f"Classified as Safe (score: {breakdown.recommendation_score:.0f}/100).",
            "target": f"Classified as Target (score: {breakdown.recommendation_score:.0f}/100).",
            "ambitious": f"Classified as Ambitious (score: {breakdown.recommendation_score:.0f}/100).",
        }
        return tier_messages.get(breakdown.tier, "")

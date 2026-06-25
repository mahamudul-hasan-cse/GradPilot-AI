"""Actionable improvement recommendations and country suggestions."""

from __future__ import annotations

from app.services.profile_intelligence.base import StudentAnalysisProfile

COUNTRY_PROFILES: list[dict] = [
    {
        "country": "United States",
        "min_gpa": 3.2,
        "min_ielts": 6.5,
        "research_bonus": True,
        "work_bonus": True,
    },
    {
        "country": "United Kingdom",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "research_bonus": False,
        "work_bonus": True,
    },
    {
        "country": "Canada",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "research_bonus": True,
        "work_bonus": True,
    },
    {
        "country": "Germany",
        "min_gpa": 2.8,
        "min_ielts": 6.0,
        "research_bonus": True,
        "work_bonus": False,
    },
    {
        "country": "Australia",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "research_bonus": False,
        "work_bonus": True,
    },
    {
        "country": "Netherlands",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "research_bonus": True,
        "work_bonus": False,
    },
    {
        "country": "Singapore",
        "min_gpa": 3.3,
        "min_ielts": 6.5,
        "research_bonus": True,
        "work_bonus": True,
    },
    {
        "country": "Ireland",
        "min_gpa": 2.9,
        "min_ielts": 6.5,
        "research_bonus": False,
        "work_bonus": True,
    },
]


class RecommendationGenerator:
    def generate(
        self,
        *,
        profile: StudentAnalysisProfile,
        admission_score: float,
        scholarship_score: float,
        weaknesses: list[str],
        missing: list[str],
        components: dict[str, float],
    ) -> dict[str, list[str]]:
        actions = self._build_actions(profile, components, missing, admission_score, scholarship_score)
        countries = self._suggest_countries(profile, admission_score)
        return {"actions": actions, "countries": countries}

    def _build_actions(
        self,
        profile: StudentAnalysisProfile,
        components: dict[str, float],
        missing: list[str],
        admission_score: float,
        scholarship_score: float,
    ) -> list[str]:
        actions: list[str] = []

        if components["language"] < 0.70:
            actions.append(
                f"Retake IELTS targeting 7.0+ (current: {profile.ielts}) to unlock more programs and scholarships"
            )
        if components["academic"] < 0.70:
            actions.append(
                "Strengthen academic narrative with relevant coursework, honors, or a strong statement of purpose"
            )
        if not profile.has_research_experience:
            actions.append(
                "Join a research lab, complete a thesis, or contribute to a faculty project before applying"
            )
        if profile.publications_count == 0 and profile.degree_level.lower() in {"phd", "doctorate"}:
            actions.append("Submit a conference paper or preprint to demonstrate research capability")
        if profile.work_experience_years < 1:
            actions.append("Gain 6–12 months of internship or industry experience in your field")
        if not profile.certifications:
            actions.append(
                "Earn 1–2 industry certifications (e.g. AWS, Google, CFA) to boost employability and scholarship appeal"
            )
        if not profile.target_intake:
            actions.append("Set a target intake (e.g. Fall 2026) and work backward on application deadlines")
        if not profile.country_preferences:
            actions.append("Shortlist 2–3 target countries based on budget, language, and career goals")
        if scholarship_score < 65:
            actions.append(
                "Apply to 3–5 merit scholarships early; highlight leadership, research, and community impact"
            )
        if admission_score < 60:
            actions.append(
                "Consider pathway programs, conditional admission, or foundation year to bridge academic gaps"
            )

        for gap in missing[:3]:
            action = f"Address missing requirement: {gap}"
            if action not in actions:
                actions.append(action)

        return actions[:8]

    def _suggest_countries(self, profile: StudentAnalysisProfile, admission_score: float) -> list[str]:
        gpa = float(profile.cgpa)
        ielts = float(profile.ielts)
        scored: list[tuple[str, float]] = []

        for entry in COUNTRY_PROFILES:
            fit = 0.0
            if gpa >= entry["min_gpa"]:
                fit += 0.40
            else:
                fit += max(0.0, (gpa / entry["min_gpa"]) * 0.25)
            if ielts >= entry["min_ielts"]:
                fit += 0.35
            else:
                fit += max(0.0, (ielts / entry["min_ielts"]) * 0.20)
            if entry["research_bonus"] and profile.has_research_experience:
                fit += 0.15
            if entry["work_bonus"] and profile.work_experience_years >= 1:
                fit += 0.10
            scored.append((entry["country"], fit))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [c for c, _ in scored[:5]]

        if profile.country_preferences:
            preferred = []
            pref_lower = [p.lower() for p in profile.country_preferences]
            for country, _ in scored:
                if any(p in country.lower() or country.lower() in p for p in pref_lower):
                    preferred.append(country)
            merged: list[str] = []
            for c in preferred + top:
                if c not in merged:
                    merged.append(c)
            return merged[:5]

        if admission_score < 55:
            return ["Germany", "Ireland", "Canada"] + [c for c in top if c not in {"Germany", "Ireland", "Canada"}][:2]

        return top

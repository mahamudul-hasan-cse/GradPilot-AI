"""University and scholarship tailoring engine."""

from __future__ import annotations

from app.services.knowledge.llm.providers import get_llm_provider


class SOPTailoringEngine:
    async def tailor_university(
        self,
        *,
        content: str,
        university_name: str,
        program_name: str,
        highlights: list[str],
    ) -> tuple[str, str]:
        highlight_str = "\n".join(f"- {h}" for h in highlights) if highlights else "- Program reputation and fit with career goals"
        user_prompt = (
            f"Tailor this Statement of Purpose for {university_name}, program: {program_name}.\n"
            f"Incorporate these university-specific points:\n{highlight_str}\n"
            f"Preserve the applicant's authentic story. Output only the tailored SOP.\n\n"
            f"Original:\n{content}"
        )
        llm = get_llm_provider()
        text = await llm.generate(
            system="You tailor SOPs to specific universities while keeping authenticity.",
            user=user_prompt,
            temperature=0.35,
        )
        reason = (
            f"Tailored for {university_name} ({program_name}) using program-specific highlights "
            f"to demonstrate fit — a key factor admissions committees evaluate."
        )
        return text.strip(), reason

    async def tailor_scholarship(
        self,
        *,
        content: str,
        scholarship_name: str,
        provider: str | None,
        eligibility_notes: str | None,
    ) -> tuple[str, str]:
        user_prompt = (
            f"Adapt this Statement of Purpose for scholarship application: {scholarship_name}.\n"
            f"Provider: {provider or 'N/A'}\n"
            f"Eligibility notes: {eligibility_notes or 'N/A'}\n"
            f"Emphasize financial need, merit, leadership, and alignment with scholarship mission.\n"
            f"Output only the adapted essay.\n\nOriginal:\n{content}"
        )
        llm = get_llm_provider()
        text = await llm.generate(
            system="You adapt SOPs for scholarship applications while maintaining authenticity.",
            user=user_prompt,
            temperature=0.35,
        )
        reason = (
            f"Adapted for scholarship '{scholarship_name}' to highlight eligibility criteria "
            f"and mission alignment required by funding committees."
        )
        return text.strip(), reason

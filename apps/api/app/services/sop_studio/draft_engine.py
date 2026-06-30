"""AI SOP draft generation."""

from __future__ import annotations

from app.services.knowledge.llm.providers import get_llm_provider


class SOPDraftEngine:
    SYSTEM = (
        "You are an expert admissions essay coach. Write compelling, authentic Statements of Purpose. "
        "Use clear structure: opening hook, academic background, research/work experience, "
        "why this program, career goals, conclusion. Avoid clichés. Be specific."
    )

    async def generate(
        self,
        *,
        student_context: str,
        university_name: str | None,
        program_name: str | None,
        scholarship_name: str | None,
        themes: list[str],
        tone: str,
        target_word_count: int,
        extra_prompt: str | None,
    ) -> tuple[str, str]:
        target = university_name or scholarship_name or "the target program"
        program = program_name or "the graduate program"
        theme_str = ", ".join(themes) if themes else "academic growth and career impact"

        user_prompt = (
            f"Write a Statement of Purpose for {target}, program: {program}.\n"
            f"Target length: ~{target_word_count} words. Tone: {tone}.\n"
            f"Themes to emphasize: {theme_str}.\n"
            f"Student context:\n{student_context}\n"
        )
        if extra_prompt:
            user_prompt += f"\nAdditional instructions: {extra_prompt}\n"
        user_prompt += "\nOutput only the SOP body text with paragraph breaks."

        llm = get_llm_provider()
        text = await llm.generate(system=self.SYSTEM, user=user_prompt, temperature=0.4)
        text = text.strip()
        reason = (
            f"Draft generated for {target} emphasizing {theme_str} "
            f"based on your Digital Twin profile and target word count of {target_word_count}."
        )
        return text, reason

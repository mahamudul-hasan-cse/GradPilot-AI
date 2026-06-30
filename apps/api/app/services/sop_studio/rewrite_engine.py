"""AI SOP rewrite engine."""

from __future__ import annotations

from app.services.knowledge.llm.providers import get_llm_provider


class SOPRewriteEngine:
    SYSTEM = (
        "You are an expert editor for graduate school Statements of Purpose. "
        "Rewrite text per instructions while preserving the applicant's authentic voice and facts."
    )

    async def rewrite(self, *, content: str, instruction: str, section: str | None) -> tuple[str, str]:
        user_prompt = f"Instruction: {instruction}\n"
        if section:
            user_prompt += f"Focus on section: {section}\n"
        user_prompt += f"\nOriginal text:\n{content}\n\nOutput only the rewritten text."

        llm = get_llm_provider()
        text = await llm.generate(system=self.SYSTEM, user=user_prompt, temperature=0.3)
        reason = f"Rewrite applied: {instruction}" + (f" (section: {section})" if section else "")
        return text.strip(), reason

"""Answer validation — structure, citations, and safety checks."""

from __future__ import annotations

from app.services.knowledge.types import Citation, KnowledgeChunk


class AnswerValidator:
    def validate(
        self,
        answer: str,
        *,
        question: str,
        chunks: list[KnowledgeChunk],
        citations: list[Citation],
        confidence: float,
        hallucination_risk: str,
    ) -> tuple[bool, list[str]]:
        issues: list[str] = []

        if not answer or len(answer.strip()) < 20:
            issues.append("Answer too short")

        if not chunks:
            if "don't have" not in answer.lower() and "insufficient" not in answer.lower():
                issues.append("Answer provided without retrieved context")

        if chunks and not citations:
            issues.append("Missing source citations")

        if hallucination_risk == "high" and confidence < 0.5:
            issues.append("High hallucination risk with low confidence")

        if len(answer) > 5000:
            issues.append("Answer exceeds maximum length")

        passed = len(issues) == 0 or (
            len(issues) == 1 and issues[0] == "Missing source citations" and chunks
        )
        return passed, issues

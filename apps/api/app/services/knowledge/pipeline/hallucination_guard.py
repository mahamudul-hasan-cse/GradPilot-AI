"""Hallucination detection — verify answer grounding in context."""

from __future__ import annotations

import re

from app.services.knowledge.types import KnowledgeChunk

HALLUCINATION_PATTERNS = [
    r"\b(I think|probably|maybe|might be)\b",
    r"\b(as an AI language model)\b",
]

ENTITY_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")


class HallucinationGuard:
    def assess(self, answer: str, chunks: list[KnowledgeChunk]) -> tuple[str, float]:
        if not chunks:
            return "high", 0.2

        context_blob = " ".join(f"{c.title} {c.content}" for c in chunks).lower()
        answer_lower = answer.lower()

        unsupported_entities = 0
        checked = 0
        for match in ENTITY_PATTERN.findall(answer):
            entity = match.strip()
            if len(entity) < 4 or entity.lower() in {"gradpilot", "source", "united", "fall", "spring"}:
                continue
            checked += 1
            if entity.lower() not in context_blob:
                unsupported_entities += 1

        hedge_hits = sum(1 for p in HALLUCINATION_PATTERNS if re.search(p, answer_lower, re.I))
        grounding_ratio = self._token_overlap(answer_lower, context_blob)

        risk_score = 0.0
        if checked:
            risk_score += (unsupported_entities / checked) * 0.5
        risk_score += hedge_hits * 0.1
        risk_score += max(0.0, 0.4 - grounding_ratio * 0.4)

        if risk_score >= 0.45:
            return "high", round(1 - risk_score, 3)
        if risk_score >= 0.25:
            return "medium", round(1 - risk_score, 3)
        return "low", round(1 - risk_score, 3)

    def _token_overlap(self, answer: str, context: str) -> float:
        answer_tokens = set(re.findall(r"[a-z0-9]{4,}", answer))
        if not answer_tokens:
            return 0.0
        context_tokens = set(re.findall(r"[a-z0-9]{4,}", context))
        return len(answer_tokens & context_tokens) / len(answer_tokens)

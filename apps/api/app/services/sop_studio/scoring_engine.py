"""AI SOP scoring engine."""

from __future__ import annotations

import re

from app.schemas.sop_studio import SOPScoreBreakdown
from app.services.sop_studio.utils import count_words


class SOPScoringEngine:
    def score(self, content: str, *, target_word_count: int = 750) -> SOPScoreBreakdown:
        words = count_words(content)
        paragraphs = [p for p in content.split("\n\n") if p.strip()]

        clarity = self._score_clarity(content)
        structure = self._score_structure(paragraphs)
        uniqueness = self._score_uniqueness(content)
        program_fit = self._score_program_fit(content)
        length_score = self._score_length(words, target_word_count)

        overall = round((clarity * 0.25 + structure * 0.25 + uniqueness * 0.2 + program_fit * 0.2 + length_score * 0.1), 1)

        feedback = []
        if words < target_word_count * 0.7:
            feedback.append(f"Essay is short ({words} words vs target {target_word_count}) — expand with specific examples.")
        if words > target_word_count * 1.3:
            feedback.append(f"Essay exceeds target length ({words} words) — tighten prose.")
        if structure < 70:
            feedback.append("Add clearer paragraph structure: hook, background, fit, goals, conclusion.")
        if uniqueness < 60:
            feedback.append("Reduce generic phrases; add personal anecdotes and specific achievements.")

        reasons = {
            "clarity": "Based on sentence length variance and readability patterns.",
            "structure": f"Evaluated {len(paragraphs)} paragraphs for SOP narrative arc.",
            "uniqueness": "Penalizes clichés and rewards specific details and metrics.",
            "program_fit": "Checks for program-specific language and future goals alignment.",
            "overall": "Weighted composite of clarity, structure, uniqueness, fit, and length.",
        }

        return SOPScoreBreakdown(
            overall=overall,
            clarity=clarity,
            structure=structure,
            uniqueness=uniqueness,
            program_fit=program_fit,
            feedback=feedback,
            reasons=reasons,
        )

    def _score_clarity(self, content: str) -> float:
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 30.0
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if 12 <= avg_len <= 25:
            return 90.0
        if avg_len > 35:
            return 55.0
        return 75.0

    def _score_structure(self, paragraphs: list[str]) -> float:
        n = len(paragraphs)
        if n >= 5:
            return 92.0
        if n >= 3:
            return 78.0
        return 50.0

    def _score_uniqueness(self, content: str) -> float:
        cliches = ["passionate", "since childhood", "dream", "prestigious", "world-class", "cutting-edge"]
        lower = content.lower()
        hits = sum(1 for c in cliches if c in lower)
        specific = len(re.findall(r"\d+", content))
        base = 80 - hits * 8 + min(15, specific * 3)
        return max(30.0, min(95.0, float(base)))

    def _score_program_fit(self, content: str) -> float:
        keywords = ["program", "research", "faculty", "university", "career", "goal", "contribute"]
        lower = content.lower()
        hits = sum(1 for k in keywords if k in lower)
        return min(95.0, 40.0 + hits * 8)

    def _score_length(self, words: int, target: int) -> float:
        ratio = words / target if target else 1
        if 0.85 <= ratio <= 1.15:
            return 95.0
        if 0.7 <= ratio <= 1.3:
            return 75.0
        return 50.0

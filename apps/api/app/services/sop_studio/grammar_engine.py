"""Grammar review engine — rule-based checks with optional LLM polish."""

from __future__ import annotations

import re

from app.schemas.sop_studio import SOPGrammarIssue
from app.services.knowledge.llm.providers import get_llm_provider


class SOPGrammarEngine:
    RULES: list[tuple[str, str, str]] = [
        (r"\bi\b", "I", "Capitalize first-person pronoun 'I'."),
        (r"\s{2,}", " ", "Remove extra spaces between words."),
        (r"\.{2,}", ".", "Replace multiple periods with a single period."),
        (r"\bvery unique\b", "distinctive", "Avoid 'very unique' — use a stronger adjective."),
        (r"\bin conclusion\b", "[consider a stronger closing]", "Overused phrase — consider a more specific closing."),
        (r"\bdue to the fact that\b", "because", "Use concise phrasing: 'because' instead of 'due to the fact that'."),
    ]

    async def review(self, content: str) -> tuple[str, list[SOPGrammarIssue]]:
        issues: list[SOPGrammarIssue] = []
        corrected = content

        for pattern, replacement, reason in self.RULES:
            if re.search(pattern, corrected, re.I):
                issues.append(SOPGrammarIssue(
                    issue=f"Pattern: {pattern}",
                    suggestion=replacement,
                    reason=reason,
                ))
                corrected = re.sub(pattern, replacement, corrected, flags=re.I)

        if len(issues) == 0:
            llm = get_llm_provider()
            polished = await llm.generate(
                system="Fix grammar and punctuation only. Output corrected text only.",
                user=f"Text:\n{content}",
                temperature=0.1,
            )
            if polished.strip() != content.strip():
                issues.append(SOPGrammarIssue(
                    issue="LLM grammar polish",
                    suggestion="See corrected text",
                    reason="AI detected grammar or punctuation improvements beyond rule-based checks.",
                ))
                corrected = polished.strip()

        return corrected, issues

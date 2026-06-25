"""Query rewriting for improved retrieval."""

from __future__ import annotations

import re

STUDY_ABROAD_EXPANSIONS = {
    "gpa": "GPA CGPA grade point average academic requirements",
    "ielts": "IELTS English language proficiency test score",
    "toefl": "TOEFL English language test",
    "sop": "statement of purpose personal statement essay",
    "lor": "letter of recommendation reference",
    "visa": "student visa immigration requirements",
    "scholarship": "scholarship funding financial aid grant",
    "masters": "masters graduate postgraduate degree",
    "phd": "PhD doctorate doctoral research degree",
    "usa": "United States America US universities",
    "uk": "United Kingdom Britain universities",
    "canada": "Canada Canadian universities immigration",
}


class QueryRewriter:
    def rewrite(self, query: str, *, conversation_context: str | None = None) -> str:
        normalized = query.strip()
        if not normalized:
            return query

        expanded_terms: list[str] = []
        lower = normalized.lower()
        for keyword, expansion in STUDY_ABROAD_EXPANSIONS.items():
            if re.search(rf"\b{re.escape(keyword)}\b", lower):
                expanded_terms.append(expansion)

        parts = [normalized]
        if expanded_terms:
            parts.append(" ".join(expanded_terms))
        if conversation_context:
            context_snippet = conversation_context[-300:].strip()
            if context_snippet:
                parts.append(context_snippet)

        return " ".join(parts)

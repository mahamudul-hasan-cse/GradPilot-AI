"""Source attribution and citation generation."""

from __future__ import annotations

import re

from app.services.knowledge.types import Citation, KnowledgeChunk


class CitationGenerator:
    def generate(self, answer: str, chunks: list[KnowledgeChunk]) -> list[Citation]:
        citations: list[Citation] = []
        referenced = self._extract_source_refs(answer)

        for idx, chunk in enumerate(chunks, start=1):
            if referenced and idx not in referenced:
                continue
            excerpt = chunk.content[:280].strip()
            if len(chunk.content) > 280:
                excerpt += "…"
            citations.append(
                Citation(
                    index=idx,
                    document_id=chunk.document_id,
                    source_type=chunk.source_type,
                    title=chunk.title,
                    excerpt=excerpt,
                    source_id=chunk.source_id,
                )
            )

        if not citations and chunks:
            for idx, chunk in enumerate(chunks[:3], start=1):
                citations.append(
                    Citation(
                        index=idx,
                        document_id=chunk.document_id,
                        source_type=chunk.source_type,
                        title=chunk.title,
                        excerpt=chunk.content[:280],
                        source_id=chunk.source_id,
                    )
                )
        return citations

    def _extract_source_refs(self, answer: str) -> set[int]:
        return {int(m) for m in re.findall(r"\[Source\s+(\d+)\]", answer, re.IGNORECASE)}

    def inject_inline_citations(self, answer: str, citations: list[Citation]) -> str:
        if citations:
            footer = "\n\n**Sources:**\n" + "\n".join(
                f"- [{c.index}] {c.title} ({c.source_type})" for c in citations
            )
            if "**Sources:**" not in answer:
                return answer.rstrip() + footer
        return answer

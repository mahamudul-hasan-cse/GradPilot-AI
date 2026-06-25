"""Context building and compression for LLM prompts."""

from __future__ import annotations

from app.services.knowledge.types import KnowledgeChunk


class ContextBuilder:
    def __init__(self, max_chars: int = 6000) -> None:
        self.max_chars = max_chars

    def build(self, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return "No relevant context found in the GradPilot knowledge base."

        parts: list[str] = []
        total = 0
        for i, chunk in enumerate(chunks, start=1):
            block = (
                f"[Source {i}] ({chunk.source_type}) {chunk.title}\n"
                f"{chunk.content.strip()}\n"
                f"Ref: {chunk.citation_key}\n"
            )
            if total + len(block) > self.max_chars:
                remaining = self.max_chars - total
                if remaining > 200:
                    parts.append(block[:remaining] + "…")
                break
            parts.append(block)
            total += len(block)
        return "\n---\n".join(parts)


class ContextCompressor:
    """Extractive compression — keep highest-scoring sentences within budget."""

    def compress(self, chunks: list[KnowledgeChunk], *, max_chars: int = 4000) -> list[KnowledgeChunk]:
        if not chunks:
            return chunks
        compressed: list[KnowledgeChunk] = []
        used = 0
        for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
            sentences = [s.strip() for s in chunk.content.replace("\n", " ").split(". ") if s.strip()]
            kept: list[str] = []
            for sentence in sentences[:5]:
                if used + len(sentence) > max_chars:
                    break
                kept.append(sentence)
                used += len(sentence)
            if kept:
                new_chunk = KnowledgeChunk(
                    document_id=chunk.document_id,
                    source_type=chunk.source_type,
                    source_id=chunk.source_id,
                    title=chunk.title,
                    content=". ".join(kept),
                    score=chunk.score,
                    metadata=chunk.metadata,
                )
                compressed.append(new_chunk)
            if used >= max_chars:
                break
        return compressed or chunks[:3]

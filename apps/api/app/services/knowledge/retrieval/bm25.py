"""BM25 keyword scoring for hybrid retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter

from app.services.knowledge.types import KnowledgeChunk

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


class BM25Scorer:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def score(self, query: str, chunks: list[KnowledgeChunk]) -> list[tuple[KnowledgeChunk, float]]:
        if not chunks:
            return []
        query_terms = tokenize(query)
        if not query_terms:
            return [(c, 0.0) for c in chunks]

        doc_terms = [tokenize(f"{c.title} {c.content}") for c in chunks]
        avg_dl = sum(len(d) for d in doc_terms) / len(doc_terms) or 1.0
        df: Counter[str] = Counter()
        for terms in doc_terms:
            for term in set(terms):
                df[term] += 1
        n_docs = len(chunks)

        scored: list[tuple[KnowledgeChunk, float]] = []
        for chunk, terms in zip(chunks, doc_terms, strict=True):
            tf = Counter(terms)
            dl = len(terms) or 1
            total = 0.0
            for term in query_terms:
                if term not in tf:
                    continue
                idf = math.log(1 + (n_docs - df[term] + 0.5) / (df[term] + 0.5))
                freq = tf[term]
                denom = freq + self.k1 * (1 - self.b + self.b * dl / avg_dl)
                total += idf * (freq * (self.k1 + 1)) / denom
            scored.append((chunk, total))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

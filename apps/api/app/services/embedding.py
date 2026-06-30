"""Embedding generation for semantic search.

Phase 1 uses deterministic local embeddings so local development and production
do not depend on OpenAI. The interface is unchanged for retrieval code.
"""

import hashlib
import math
import re
from abc import ABC, abstractmethod

VECTOR_SIZE = 384


def _normalize(vec: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / magnitude for v in vec]


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass

    @property
    def vector_size(self) -> int:
        return VECTOR_SIZE


class FallbackEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embeddings for dev/test without OpenAI."""

    def embed(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        vec = [0.0] * VECTOR_SIZE
        if not tokens:
            return vec
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            for i in range(VECTOR_SIZE):
                vec[i] += (digest[i % len(digest)] / 255.0) - 0.5
        return _normalize(vec)


def get_embedding_provider() -> EmbeddingProvider:
    return FallbackEmbeddingProvider()

"""Embedding generation for university semantic search."""

import hashlib
import math
import re
from abc import ABC, abstractmethod

from app.core.config import settings

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


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        from langchain_openai import OpenAIEmbeddings

        self._client = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self._fallback = FallbackEmbeddingProvider()

    @property
    def vector_size(self) -> int:
        return VECTOR_SIZE

    def embed(self, text: str) -> list[float]:
        try:
            vector = self._client.embed_query(text)
            if len(vector) != VECTOR_SIZE:
                return _normalize(vector[:VECTOR_SIZE] + [0.0] * max(0, VECTOR_SIZE - len(vector)))
            return _normalize(vector)
        except Exception:
            return self._fallback.embed(text)


def get_embedding_provider() -> EmbeddingProvider:
    if settings.openai_api_key:
        return OpenAIEmbeddingProvider()
    return FallbackEmbeddingProvider()

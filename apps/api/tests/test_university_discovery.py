from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.discovery import (
    RecommendUniversitiesRequest,
    RecommendUniversitiesResponse,
    RecommendationTier,
    UniversitySearchResult,
)
from app.services.embedding import FallbackEmbeddingProvider
from app.services.university_discovery import UniversityDiscoveryService


@pytest.mark.asyncio
async def test_recommend_universities_endpoint_mocked(client):
    mock_response = RecommendUniversitiesResponse(
        input=RecommendUniversitiesRequest(
            cgpa=Decimal("3.5"),
            ielts=Decimal("7.0"),
            budget=Decimal("50000"),
            country="United States",
            major="Computer Science",
        ),
        recommendations=RecommendationTier(),
        total_candidates_evaluated=3,
    )
    with patch(
        "app.api.v1.endpoints.discovery.UniversityDiscoveryService.recommend",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            "/api/v1/recommend-universities",
            json={
                "cgpa": 3.5,
                "ielts": 7.0,
                "budget": 50000,
                "country": "United States",
                "major": "Computer Science",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["total_candidates_evaluated"] == 3
    assert "recommendations" in data


@pytest.mark.asyncio
async def test_recommend_universities_invalid_cgpa(client):
    response = await client.post(
        "/api/v1/recommend-universities",
        json={
            "cgpa": 5.0,
            "ielts": 7.0,
            "budget": 50000,
            "major": "Computer Science",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_semantic_search_endpoint_mocked(client):
    mock_response = UniversitySearchResult(
        items=[],
        total=0,
        skip=0,
        limit=5,
        search_mode="semantic",
    )
    with patch(
        "app.api.v1.endpoints.universities.UniversityDiscoveryService.semantic_search",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            "/api/v1/universities/semantic-search",
            json={"query": "affordable computer science masters in Canada", "limit": 5},
        )
    assert response.status_code == 200
    assert response.json()["search_mode"] == "semantic"


@pytest.mark.asyncio
async def test_university_search_endpoint_mocked(client):
    mock_response = UniversitySearchResult(
        items=[],
        total=0,
        skip=0,
        limit=5,
        search_mode="keyword",
    )
    with patch(
        "app.api.v1.endpoints.universities.UniversityDiscoveryService.keyword_search",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            "/api/v1/universities/search",
            json={"query": "MIT", "limit": 5},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_university_filter_endpoint_mocked(client):
    mock_response = UniversitySearchResult(
        items=[],
        total=0,
        skip=0,
        limit=20,
        search_mode="filter",
    )
    with patch(
        "app.api.v1.endpoints.universities.UniversityDiscoveryService.filter_universities",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.get(
            "/api/v1/universities/filter",
            params={"country": "Canada", "max_tuition": 50000, "scholarships_available": True},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_discovery_recommend_service_logic():
    mock_db = MagicMock()
    service = UniversityDiscoveryService(mock_db)
    university = SimpleNamespace(
        id=uuid4(),
        name="Test University",
        country="United States",
        city="Boston",
        website="https://example.edu",
        ranking=100,
        description="Test",
        logo_url=None,
        tuition_fee=Decimal("30000"),
        application_fee=Decimal("50"),
        minimum_gpa=Decimal("3.0"),
        minimum_ielts=Decimal("6.5"),
        minimum_toefl=80,
        deadline=None,
        programs=["MS Computer Science"],
        scholarships_available=True,
        majors=["Computer Science"],
        is_active=True,
        created_at="2026-01-01T00:00:00Z",
        search_text="Test University CS",
    )

    with patch.object(
        service.university_repo,
        "get_candidates_for_recommendation",
        new_callable=AsyncMock,
        return_value=[university],
    ):
        result = await service.recommend(
            RecommendUniversitiesRequest(
                cgpa=Decimal("3.5"),
                ielts=Decimal("7.0"),
                budget=Decimal("40000"),
                country="United States",
                major="Computer Science",
            )
        )

    assert result.total_candidates_evaluated == 1
    total_recommended = (
        len(result.recommendations.safe)
        + len(result.recommendations.target)
        + len(result.recommendations.ambitious)
    )
    assert total_recommended >= 1


class TestEmbeddingProvider:
    def test_fallback_embedding_dimension(self):
        provider = FallbackEmbeddingProvider()
        vector = provider.embed("computer science masters canada")
        assert len(vector) == provider.vector_size

    def test_fallback_embedding_deterministic(self):
        provider = FallbackEmbeddingProvider()
        a = provider.embed("MIT engineering")
        b = provider.embed("MIT engineering")
        assert a == b

    def test_fallback_embedding_different_text(self):
        provider = FallbackEmbeddingProvider()
        a = provider.embed("MIT")
        b = provider.embed("Oxford")
        assert a != b


class TestQdrantVectorStore:
    def test_upsert_and_search_mocked(self):
        from app.services.qdrant_store import QdrantVectorStore

        mock_client = MagicMock()
        mock_client.get_collections.return_value = MagicMock(collections=[])
        mock_client.search.return_value = [
            MagicMock(payload={"university_id": str(uuid4())}, score=0.92),
        ]

        store = QdrantVectorStore(client=mock_client)
        uid = uuid4()
        store.upsert_university(uid, name="Test U", country="Canada", search_text="CS masters")
        mock_client.upsert.assert_called_once()

        results = store.semantic_search("computer science", limit=5)
        assert len(results) == 1
        assert results[0][1] == pytest.approx(0.92)

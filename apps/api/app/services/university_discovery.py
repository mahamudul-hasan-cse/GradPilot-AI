from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.university import University
from app.repositories.university import UniversityFilterParams, UniversityRepository
from app.schemas.discovery import (
    RankingScoreBreakdown,
    RecommendUniversitiesRequest,
    RecommendUniversitiesResponse,
    RecommendationTier,
    ScoredUniversityResponse,
    SemanticSearchRequest,
    UniversityFilterRequest,
    UniversitySearchRequest,
    UniversitySearchResult,
)
from app.schemas.university import UniversityResponse
from app.services.qdrant_store import QdrantVectorStore
from app.services.university_ranking import StudentProfile, rank_university


class UniversityDiscoveryService:
    def __init__(
        self,
        db: AsyncSession,
        vector_store: QdrantVectorStore | None = None,
    ):
        self.university_repo = UniversityRepository(db)
        self.vector_store = vector_store or QdrantVectorStore()

    def _to_scored(
        self,
        university: University,
        profile: StudentProfile,
        *,
        semantic_score: float | None = None,
    ) -> ScoredUniversityResponse:
        breakdown = rank_university(university, profile)
        base = UniversityResponse.model_validate(university)
        return ScoredUniversityResponse(
            **base.model_dump(),
            match_score=breakdown.composite_score,
            semantic_score=semantic_score,
            ranking_breakdown=RankingScoreBreakdown(
                gpa_match=breakdown.gpa_match,
                ielts_match=breakdown.ielts_match,
                budget_match=breakdown.budget_match,
                ranking_preference=breakdown.ranking_preference,
                scholarship_availability=breakdown.scholarship_availability,
                composite_score=breakdown.composite_score,
                tier=breakdown.tier,
            ),
        )

    async def filter_universities(self, filters: UniversityFilterRequest) -> UniversitySearchResult:
        params = UniversityFilterParams(
            country=filters.country,
            city=filters.city,
            major=filters.major,
            min_ranking=filters.min_ranking,
            max_ranking=filters.max_ranking,
            max_tuition=filters.max_tuition,
            min_tuition=filters.min_tuition,
            max_gpa_required=filters.max_gpa_required,
            min_gpa_required=filters.min_gpa_required,
            max_ielts_required=filters.max_ielts_required,
            scholarships_available=filters.scholarships_available,
            skip=filters.skip,
            limit=filters.limit,
        )
        universities, total = await self.university_repo.filter_universities(params)
        profile = StudentProfile(cgpa=Decimal("3.0"), ielts=Decimal("6.5"), budget=Decimal("50000"))
        items = [self._to_scored(u, profile) for u in universities]
        return UniversitySearchResult(
            items=items,
            total=total,
            skip=filters.skip,
            limit=filters.limit,
            search_mode="filter",
        )

    async def keyword_search(self, request: UniversitySearchRequest) -> UniversitySearchResult:
        universities = await self.university_repo.search_text_query(
            request.query,
            country=request.country,
            major=request.major,
            limit=request.limit + request.skip,
        )
        paginated = universities[request.skip : request.skip + request.limit]
        profile = StudentProfile(cgpa=Decimal("3.0"), ielts=Decimal("6.5"), budget=Decimal("50000"))
        items = [self._to_scored(u, profile) for u in paginated]
        return UniversitySearchResult(
            items=items,
            total=len(universities),
            skip=request.skip,
            limit=request.limit,
            search_mode="keyword",
        )

    async def semantic_search(self, request: SemanticSearchRequest) -> UniversitySearchResult:
        profile = StudentProfile(cgpa=Decimal("3.0"), ielts=Decimal("6.5"), budget=Decimal("50000"))
        vector_hits = self.vector_store.semantic_search(
            request.query,
            limit=request.limit * 2,
            country=request.country,
        )

        if vector_hits:
            ids = [uid for uid, _ in vector_hits]
            score_map = {uid: score for uid, score in vector_hits}
            universities = await self.university_repo.get_by_ids(ids)
            if request.major:
                major_lower = request.major.lower()
                universities = [
                    u
                    for u in universities
                    if any(major_lower in (m or "").lower() for m in (u.majors or []))
                    or any(major_lower in (p or "").lower() for p in (u.programs or []))
                    or major_lower in (u.search_text or "").lower()
                ]
            items = [
                self._to_scored(u, profile, semantic_score=score_map.get(u.id))
                for u in universities[: request.limit]
            ]
            if items:
                return UniversitySearchResult(
                    items=items,
                    total=len(items),
                    skip=0,
                    limit=request.limit,
                    search_mode="semantic",
                )

        fallback = await self.university_repo.search_text_query(
            request.query,
            country=request.country,
            major=request.major,
            limit=request.limit,
        )
        items = [self._to_scored(u, profile, semantic_score=0.5) for u in fallback]
        return UniversitySearchResult(
            items=items,
            total=len(items),
            skip=0,
            limit=request.limit,
            search_mode="semantic_fallback",
        )

    async def recommend(self, request: RecommendUniversitiesRequest) -> RecommendUniversitiesResponse:
        profile = StudentProfile(
            cgpa=request.cgpa,
            ielts=request.ielts,
            budget=request.budget,
        )
        candidates = await self.university_repo.get_candidates_for_recommendation(
            country=request.country,
            major=request.major,
            max_budget=request.budget * Decimal("1.5"),
            limit=100,
        )

        scored: list[ScoredUniversityResponse] = []
        for university in candidates:
            scored.append(self._to_scored(university, profile))

        scored.sort(key=lambda item: item.match_score, reverse=True)

        tiers: dict[str, list[ScoredUniversityResponse]] = {
            "safe": [],
            "target": [],
            "ambitious": [],
        }
        for item in scored:
            tier = item.ranking_breakdown.tier
            if len(tiers[tier]) < request.limit_per_tier:
                tiers[tier].append(item)

        return RecommendUniversitiesResponse(
            input=request,
            recommendations=RecommendationTier(
                safe=tiers["safe"],
                target=tiers["target"],
                ambitious=tiers["ambitious"],
            ),
            total_candidates_evaluated=len(scored),
        )

    async def index_university(self, university: University) -> None:
        search_text = university.search_text or university.build_search_text()
        self.vector_store.upsert_university(
            university.id,
            name=university.name,
            country=university.country,
            search_text=search_text,
            payload={
                "city": university.city,
                "ranking": university.ranking,
                "majors": university.majors or [],
            },
        )

    async def index_all_universities(self) -> int:
        universities = await self.university_repo.get_all_active()
        for university in universities:
            await self.index_university(university)
        return len(universities)

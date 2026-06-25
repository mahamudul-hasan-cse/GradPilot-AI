"""PostgreSQL and Qdrant loaders for ingested data."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.schemas import NormalizedUniversityData
from app.models.scholarship import Scholarship
from app.models.university import Program, University
from app.services.qdrant_store import QdrantVectorStore


class PostgresLoader:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_university(
        self,
        data: NormalizedUniversityData,
        *,
        quality_score: float,
        existing_id: UUID | None = None,
    ) -> University:
        university: University | None = None
        if existing_id:
            university = await self.db.get(University, existing_id)

        if university is None and data.external_id:
            result = await self.db.execute(
                select(University).where(University.external_id == data.external_id)
            )
            university = result.scalar_one_or_none()

        if university is None:
            university = University()
            self.db.add(university)

        university.name = data.name
        university.country = data.country
        university.city = data.city
        university.website = data.website
        university.description = data.description
        university.ranking = data.ranking
        university.tuition_fee = data.tuition_fee
        university.application_fee = data.application_fee
        university.minimum_gpa = data.minimum_gpa
        university.minimum_ielts = data.minimum_ielts
        university.minimum_toefl = data.minimum_toefl
        university.deadline = data.deadline
        university.programs = data.programs or None
        university.majors = data.majors or None
        university.scholarships_available = data.scholarships_available
        university.source_url = data.source_url
        university.external_id = data.external_id
        university.content_hash = data.content_hash
        university.data_quality_score = Decimal(str(round(quality_score, 2)))
        university.last_ingested_at = datetime.now(UTC)
        university.search_text = self._build_search_text(data)
        university.is_active = True

        await self.db.flush()
        await self._sync_programs(university, data)
        await self._sync_scholarships(university, data)
        await self.db.refresh(university)
        return university

    async def _sync_programs(self, university: University, data: NormalizedUniversityData) -> None:
        if not data.program_records:
            return
        for existing in list(university.program_records):
            await self.db.delete(existing)
        await self.db.flush()

        for prog in data.program_records[:50]:
            self.db.add(
                Program(
                    university_id=university.id,
                    name=prog.name[:500],
                    degree_type=prog.degree_type or "Masters",
                    field_of_study=prog.field_of_study,
                    tuition_fee=prog.tuition_fee or data.tuition_fee,
                    tuition_currency=prog.tuition_currency or "USD",
                    duration_months=prog.duration_months,
                    description=prog.description,
                    requirements=prog.requirements,
                    application_deadline=prog.application_deadline or data.deadline,
                )
            )

    async def _sync_scholarships(self, university: University, data: NormalizedUniversityData) -> None:
        for idx, scholarship in enumerate(data.scholarships[:20]):
            external_id = f"{data.external_id}:scholarship:{idx}" if data.external_id else None
            existing = None
            if external_id:
                result = await self.db.execute(
                    select(Scholarship).where(Scholarship.external_id == external_id)
                )
                existing = result.scalar_one_or_none()
            if existing is None:
                existing = Scholarship(
                    title=scholarship.title[:500],
                    provider=scholarship.provider or university.name,
                    university_id=university.id,
                    external_id=external_id,
                )
                self.db.add(existing)
            existing.country = data.country
            existing.amount = scholarship.amount
            existing.currency = scholarship.currency or "USD"
            existing.description = scholarship.description
            existing.eligibility = scholarship.eligibility
            existing.deadline = scholarship.deadline
            existing.application_url = scholarship.application_url or data.website
            existing.source_url = data.source_url
            existing.is_active = True

    def _build_search_text(self, data: NormalizedUniversityData) -> str:
        return " ".join(
            filter(
                None,
                [data.name, data.country, data.city or "", data.description or "",
                 " ".join(data.programs), " ".join(data.majors)],
            )
        )


class QdrantLoader:
    def __init__(self, vector_store: QdrantVectorStore | None = None):
        self.vector_store = vector_store or QdrantVectorStore()

    def index_university(self, university: University) -> None:
        self.vector_store.upsert_university(
            university.id,
            name=university.name,
            country=university.country,
            search_text=university.search_text or university.build_search_text(),
            payload={
                "city": university.city,
                "ranking": university.ranking,
                "majors": university.majors or [],
                "quality_score": float(university.data_quality_score or 0),
            },
        )

    def index_batch(self, universities: list[University]) -> int:
        for university in universities:
            self.index_university(university)
        return len(universities)

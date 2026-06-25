"""University deduplication at scale."""

from __future__ import annotations

import hashlib
import re
from uuid import UUID

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.normalizer import extract_domain, normalize_country, normalize_name
from app.ingestion.schemas import DedupResult, NormalizedUniversityData
from app.models.ingestion import UniversityFingerprint


def build_fingerprint_hash(name: str, country: str, website: str | None) -> str:
    normalized = normalize_name(name).lower()
    country_norm = normalize_country(country).lower()
    domain = extract_domain(website) or ""
    raw = f"{normalized}|{country_norm}|{domain}"
    return hashlib.sha256(raw.encode()).hexdigest()


class UniversityDeduplicator:
    FUZZY_THRESHOLD = 92

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_duplicate(self, data: NormalizedUniversityData) -> DedupResult:
        fp_hash = build_fingerprint_hash(data.name, data.country, data.website)

        exact = await self.db.execute(
            select(UniversityFingerprint).where(UniversityFingerprint.fingerprint_hash == fp_hash)
        )
        match = exact.scalar_one_or_none()
        if match:
            return DedupResult(
                is_duplicate=True,
                duplicate_of_id=match.university_id,
                match_type="hash",
                confidence=1.0,
            )

        domain = extract_domain(data.website)
        if domain:
            domain_matches = await self.db.execute(
                select(UniversityFingerprint).where(UniversityFingerprint.website_domain == domain)
            )
            for candidate in domain_matches.scalars().all():
                return DedupResult(
                    is_duplicate=True,
                    duplicate_of_id=candidate.university_id,
                    match_type="domain",
                    confidence=0.95,
                )

        normalized = normalize_name(data.name).lower()
        country = normalize_country(data.country)
        fuzzy_candidates = await self.db.execute(
            select(UniversityFingerprint).where(UniversityFingerprint.country == country).limit(200)
        )
        for candidate in fuzzy_candidates.scalars().all():
            score = fuzz.token_sort_ratio(normalized, candidate.normalized_name.lower())
            if score >= self.FUZZY_THRESHOLD:
                return DedupResult(
                    is_duplicate=True,
                    duplicate_of_id=candidate.university_id,
                    match_type="fuzzy",
                    confidence=score / 100,
                )

        return DedupResult(is_duplicate=False)

    async def register_fingerprint(self, university_id: UUID, data: NormalizedUniversityData) -> None:
        fp = UniversityFingerprint(
            university_id=university_id,
            fingerprint_hash=build_fingerprint_hash(data.name, data.country, data.website),
            normalized_name=normalize_name(data.name),
            website_domain=extract_domain(data.website),
            country=normalize_country(data.country),
        )
        self.db.add(fp)
        await self.db.flush()

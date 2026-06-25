"""Normalize extracted university data to canonical schema."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from urllib.parse import urlparse

from app.ingestion.schemas import ExtractedUniversityData, NormalizedUniversityData

COUNTRY_ALIASES = {
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "england": "United Kingdom",
}


def normalize_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name).strip()
    cleaned = re.sub(r"\s*[\|–-]\s*(Home|Official Site|Welcome).*$", "", cleaned, flags=re.I)
    return cleaned[:500]


def normalize_country(country: str | None, fallback: str | None = None) -> str:
    if not country and fallback:
        country = fallback
    if not country:
        return "Unknown"
    key = country.strip().lower()
    return COUNTRY_ALIASES.get(key, country.strip().title())


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.netloc.lower().removeprefix("www.")
    return domain or None


def compute_content_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


class UniversityNormalizer:
    def normalize(
        self,
        extracted: ExtractedUniversityData,
        *,
        source_url: str,
        external_id: str | None = None,
        fallback_country: str | None = None,
    ) -> NormalizedUniversityData:
        name = normalize_name(extracted.name)
        country = normalize_country(extracted.country, fallback_country)
        website = extracted.website or source_url
        domain = extract_domain(website)

        program_names = [p.name for p in extracted.programs]
        majors = list({
            p.field_of_study for p in extracted.programs if p.field_of_study
        })
        if not majors:
            majors = self._infer_majors(program_names)

        tuition_values = [p.tuition_fee for p in extracted.programs if p.tuition_fee]
        tuition_fee = extracted.tuition_fee or (min(tuition_values) if tuition_values else None)

        requirements = extracted.admission_requirements
        payload = {
            "name": name,
            "country": country,
            "website": website,
            "programs": program_names,
            "tuition_fee": str(tuition_fee) if tuition_fee else None,
        }

        return NormalizedUniversityData(
            name=name,
            country=country,
            city=extracted.city,
            website=website,
            description=extracted.description,
            ranking=extracted.ranking,
            tuition_fee=tuition_fee,
            application_fee=extracted.application_fee,
            minimum_gpa=requirements.minimum_gpa if requirements else None,
            minimum_ielts=requirements.minimum_ielts if requirements else None,
            minimum_toefl=requirements.minimum_toefl if requirements else None,
            deadline=extracted.deadline,
            programs=program_names,
            majors=majors,
            scholarships_available=extracted.scholarships_available,
            program_records=extracted.programs,
            scholarships=extracted.scholarships,
            source_url=source_url,
            external_id=external_id or domain,
            content_hash=compute_content_hash(payload),
        )

    def _infer_majors(self, programs: list[str]) -> list[str]:
        majors: set[str] = set()
        patterns = {
            "Computer Science": r"computer science|informatics|software",
            "Engineering": r"engineering",
            "Business": r"business|mba|management",
            "Data Science": r"data science|analytics",
            "Medicine": r"medicine|health|public health",
        }
        combined = " ".join(programs).lower()
        for major, pattern in patterns.items():
            if re.search(pattern, combined, re.I):
                majors.add(major)
        return list(majors)

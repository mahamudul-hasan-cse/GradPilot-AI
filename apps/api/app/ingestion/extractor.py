"""Extract structured university data from HTML."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from app.ingestion.schemas import (
    ExtractedUniversityData,
    RawAdmissionRequirements,
    RawProgramData,
    RawScholarshipData,
    ScrapeResult,
)

CURRENCY_PATTERN = re.compile(r"[\$€£]?\s*([\d,]+(?:\.\d{2})?)\s*(USD|EUR|GBP|CAD|AUD)?", re.I)
GPA_PATTERN = re.compile(r"GPA[:\s]+(\d\.\d+)", re.I)
IELTS_PATTERN = re.compile(r"IELTS[:\s]+(\d(?:\.\d)?)", re.I)
TOEFL_PATTERN = re.compile(r"TOEFL[:\s]+(\d{2,3})", re.I)
DATE_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    re.I,
)
PROGRAM_PATTERN = re.compile(
    r"(Bachelor|Master|MBA|MSc|MA|MS|PhD|Doctor).{0,80}?(?:in|of)\s+[\w\s/&-]+",
    re.I,
)
SCHOLARSHIP_PATTERN = re.compile(r"scholarship|fellowship|financial aid|funding", re.I)

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def _parse_amount(text: str) -> Decimal | None:
    match = CURRENCY_PATTERN.search(text)
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def _parse_date(text: str) -> date | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    parts = match.group(0).replace(",", "").split()
    if len(parts) < 3:
        return None
    month = MONTH_MAP.get(parts[0].lower())
    if not month:
        return None
    try:
        day = int(parts[1])
        year = int(parts[2])
        return date(year, month, day)
    except ValueError:
        return None


def _extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    records = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                records.extend(data)
            elif isinstance(data, dict):
                records.append(data)
        except json.JSONDecodeError:
            continue
    return records


class UniversityExtractor:
    def extract(
        self,
        scrape: ScrapeResult,
        *,
        fallback_name: str | None = None,
        fallback_country: str | None = None,
    ) -> ExtractedUniversityData:
        if not scrape.html:
            return ExtractedUniversityData(
                name=fallback_name or "Unknown University",
                country=fallback_country,
                extraction_method="empty",
            )

        soup = BeautifulSoup(scrape.html, "lxml")
        text = soup.get_text(" ", strip=True)
        title = soup.title.string.strip() if soup.title and soup.title.string else fallback_name

        json_ld = _extract_json_ld(soup)
        description = self._extract_description(soup, json_ld)
        tuition = self._extract_tuition(text)
        programs = self._extract_programs(text, soup)
        scholarships = self._extract_scholarships(text, soup)
        requirements = self._extract_requirements(text)
        deadline = _parse_date(text)

        return ExtractedUniversityData(
            name=fallback_name or title or "Unknown University",
            country=fallback_country,
            website=scrape.url,
            description=description,
            tuition_fee=tuition,
            deadline=deadline,
            programs=programs,
            scholarships=scholarships,
            admission_requirements=requirements,
            scholarships_available=len(scholarships) > 0 or bool(SCHOLARSHIP_PATTERN.search(text)),
            raw_html_length=len(scrape.html),
            extraction_method="html_heuristic+jsonld",
        )

    def _extract_description(self, soup: BeautifulSoup, json_ld: list[dict]) -> str | None:
        for record in json_ld:
            if record.get("@type") in ("CollegeOrUniversity", "EducationalOrganization"):
                desc = record.get("description")
                if desc:
                    return str(desc)[:2000]
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return str(meta["content"])[:2000]
        return None

    def _extract_tuition(self, text: str) -> Decimal | None:
        for keyword in ("tuition", "tuition fee", "annual fee", "cost of attendance"):
            idx = text.lower().find(keyword)
            if idx >= 0:
                snippet = text[idx : idx + 80]
                amount = _parse_amount(snippet)
                if amount:
                    return amount
        return _parse_amount(text)

    def _extract_programs(self, text: str, soup: BeautifulSoup) -> list[RawProgramData]:
        found: dict[str, RawProgramData] = {}
        for match in PROGRAM_PATTERN.finditer(text):
            name = match.group(0).strip()[:200]
            if name not in found:
                degree = "Masters" if re.search(r"master|msc|ma|ms|mba", name, re.I) else "Bachelors"
                if re.search(r"phd|doctor", name, re.I):
                    degree = "PhD"
                found[name] = RawProgramData(name=name, degree_type=degree)

        for heading in soup.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text(strip=True)
            if re.search(r"program|degree|course", heading_text, re.I):
                name = heading_text[:200]
                if name not in found:
                    found[name] = RawProgramData(name=name, degree_type="Masters")
        return list(found.values())[:50]

    def _extract_scholarships(self, text: str, soup: BeautifulSoup) -> list[RawScholarshipData]:
        scholarships: list[RawScholarshipData] = []
        for heading in soup.find_all(["h2", "h3", "h4", "a"]):
            heading_text = heading.get_text(strip=True)
            if SCHOLARSHIP_PATTERN.search(heading_text) and len(heading_text) < 200:
                scholarships.append(
                    RawScholarshipData(
                        title=heading_text,
                        provider="University",
                        description=heading_text,
                    )
                )
        return scholarships[:20]

    def _extract_requirements(self, text: str) -> RawAdmissionRequirements:
        gpa = GPA_PATTERN.search(text)
        ielts = IELTS_PATTERN.search(text)
        toefl = TOEFL_PATTERN.search(text)
        return RawAdmissionRequirements(
            minimum_gpa=Decimal(gpa.group(1)) if gpa else None,
            minimum_ielts=Decimal(ielts.group(1)) if ielts else None,
            minimum_toefl=int(toefl.group(1)) if toefl else None,
        )

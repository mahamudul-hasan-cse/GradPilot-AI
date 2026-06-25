"""Unit tests for the data ingestion pipeline."""

from decimal import Decimal

import pytest

from app.ingestion.extractor import UniversityExtractor
from app.ingestion.deduplicator import build_fingerprint_hash
from app.ingestion.normalizer import UniversityNormalizer
from app.ingestion.schemas import ExtractedUniversityData, RawProgramData, ScrapeResult
from app.ingestion.validator import DataQualityValidator


SAMPLE_HTML = """
<html>
<head><title>Test University - Computer Science</title>
<meta name="description" content="Leading research university."></head>
<body>
<h2>Master of Science in Computer Science</h2>
<h3>MBA Program</h3>
<p>Tuition fee: $45,000 USD per year</p>
<p>Application deadline: December 15, 2026</p>
<p>Minimum GPA: 3.2. IELTS: 6.5. TOEFL: 90</p>
<h3>Merit Scholarship Program</h3>
<h3>International Student Fellowship</h3>
</body>
</html>
"""


class TestExtractor:
    def test_extracts_programs_and_fees(self):
        extractor = UniversityExtractor()
        scrape = ScrapeResult(url="https://test.edu", status_code=200, html=SAMPLE_HTML)
        result = extractor.extract(scrape, fallback_name="Test University", fallback_country="United States")

        assert result.name == "Test University"
        assert result.tuition_fee == Decimal("45000")
        assert len(result.programs) >= 1
        assert result.scholarships_available is True
        assert result.admission_requirements.minimum_gpa == Decimal("3.2")
        assert result.admission_requirements.minimum_ielts == Decimal("6.5")


class TestNormalizer:
    def test_normalizes_country_and_hash(self):
        normalizer = UniversityNormalizer()
        extracted = ExtractedUniversityData(
            name="Test University | Home",
            country="usa",
            website="https://www.test.edu",
            programs=[RawProgramData(name="MSc Computer Science", degree_type="Masters")],
            tuition_fee=Decimal("45000"),
        )
        normalized = normalizer.normalize(
            extracted,
            source_url="https://www.test.edu",
            external_id="test.edu",
        )
        assert normalized.country == "United States"
        assert normalized.name == "Test University"
        assert len(normalized.content_hash) == 64
        assert "Computer Science" in normalized.majors or normalized.programs


class TestValidator:
    def test_passes_quality_university(self):
        normalizer = UniversityNormalizer()
        extracted = ExtractedUniversityData(
            name="Quality University",
            country="Canada",
            website="https://quality.ca",
            programs=[RawProgramData(name="MS CS", degree_type="Masters")],
            tuition_fee=Decimal("30000"),
            description="A good school",
        )
        normalized = normalizer.normalize(extracted, source_url="https://quality.ca")
        report = DataQualityValidator().validate(normalized)
        assert report.passed is True
        assert report.score >= 50

    def test_fails_without_country(self):
        normalizer = UniversityNormalizer()
        extracted = ExtractedUniversityData(name="Bad Uni", website="https://bad.edu")
        normalized = normalizer.normalize(extracted, source_url="https://bad.edu", fallback_country=None)
        normalized.country = ""
        report = DataQualityValidator().validate(normalized)
        assert report.passed is False


class TestFingerprint:
    def test_same_university_same_hash(self):
        h1 = build_fingerprint_hash("MIT", "United States", "https://www.mit.edu")
        h2 = build_fingerprint_hash("MIT", "United States", "https://mit.edu")
        assert h1 == h2

    def test_different_university_different_hash(self):
        h1 = build_fingerprint_hash("MIT", "United States", "https://www.mit.edu")
        h2 = build_fingerprint_hash("Oxford", "United Kingdom", "https://www.ox.ac.uk")
        assert h1 != h2

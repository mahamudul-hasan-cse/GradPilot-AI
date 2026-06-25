"""Document intelligence types and extraction schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OCRResult:
    raw_text: str
    provider: str
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    signals: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    document_type: str
    fields: dict[str, Any]
    confidence: float
    field_confidence: dict[str, float] = field(default_factory=dict)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed_rules: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    document_id: str
    status: str
    classified_type: str
    extracted_fields: dict[str, Any]
    validation: ValidationResult
    confidence_score: float
    is_duplicate: bool
    version: int


EXTRACTION_SCHEMAS: dict[str, list[str]] = {
    "passport": ["name", "passport_number", "expiry_date", "nationality", "date_of_birth"],
    "transcript": ["institution", "degree", "cgpa", "courses", "graduation_year"],
    "degree_certificate": ["institution", "degree", "major", "graduation_date", "honors"],
    "cv": ["skills", "experience", "projects", "education", "contact_email"],
    "ielts_trf": ["overall_band", "listening", "reading", "writing", "speaking", "test_date", "candidate_name"],
    "toefl": ["total_score", "reading", "listening", "speaking", "writing", "test_date"],
    "gre": ["verbal", "quantitative", "analytical_writing", "total", "test_date"],
    "lor": ["recommender_name", "recommender_title", "institution", "relationship", "date"],
    "sop": ["title", "word_count", "target_program", "university", "themes"],
}

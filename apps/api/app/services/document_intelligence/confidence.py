"""Confidence scoring for document extraction."""

from __future__ import annotations

from app.services.document_intelligence.types import ClassificationResult, ExtractionResult, ValidationResult


class ConfidenceScorer:
    def score(
        self,
        *,
        classification: ClassificationResult,
        extraction: ExtractionResult,
        validation: ValidationResult,
        ocr_confidence: float = 0.0,
    ) -> float:
        class_score = classification.confidence * 0.20
        extract_score = extraction.confidence * 0.45
        ocr_score = ocr_confidence * 0.15
        validation_score = (1.0 if validation.is_valid else 0.4) * 0.20

        field_coverage = 0.0
        if extraction.field_confidence:
            field_coverage = sum(extraction.field_confidence.values()) / len(extraction.field_confidence)
        coverage_bonus = field_coverage * 0.10

        total = class_score + extract_score + ocr_score + validation_score + coverage_bonus
        if validation.errors:
            total *= 0.75
        return round(min(1.0, max(0.0, total)), 4)

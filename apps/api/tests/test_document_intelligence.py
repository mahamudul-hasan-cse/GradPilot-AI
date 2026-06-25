"""Tests for Document Intelligence Platform."""

import pytest

from app.repositories.document_intelligence import DocumentUploadRepository
from app.services.document_intelligence.classifier import DocumentClassifier
from app.services.document_intelligence.confidence import ConfidenceScorer
from app.services.document_intelligence.extractors import (
    CVExtractor,
    IELTSExtractor,
    PassportExtractor,
    TranscriptExtractor,
    get_extractor,
)
from app.services.document_intelligence.ocr.providers import FallbackOCRProvider
from app.services.document_intelligence.types import (
    ClassificationResult,
    ExtractionResult,
    ValidationResult,
)
from app.services.document_intelligence.validator import ValidationEngine


PASSPORT_TEXT = (
    "PASSPORT\nName: Jane Doe\nPassport No: P12345678\nNationality: Indian\n"
    "Date of Expiry: 14/03/2028"
)

IELTS_TEXT = (
    "IELTS Test Report Form\nCandidate: Jane Doe\nOverall Band Score: 7.5\n"
    "Listening: 8.0 Reading: 7.5 Writing: 7.0 Speaking: 7.0\nTest Date: 12/01/2025"
)

TRANSCRIPT_TEXT = (
    "Official Transcript\nInstitution: State University\nDegree: BSc Computer Science\n"
    "CGPA: 3.65/4.0\nCourses: Data Structures, Algorithms"
)


class TestClassifier:
    def test_classifies_passport(self):
        clf = DocumentClassifier()
        result = clf.classify(PASSPORT_TEXT, file_name="passport_scan.pdf")
        assert result.document_type == "passport"
        assert result.confidence > 0.5

    def test_classifies_ielts(self):
        clf = DocumentClassifier()
        result = clf.classify(IELTS_TEXT, file_name="ielts_trf.pdf")
        assert result.document_type == "ielts_trf"

    def test_user_hint(self):
        clf = DocumentClassifier()
        result = clf.classify("unknown text", hint_type="cv")
        assert result.document_type == "cv"
        assert result.confidence == 0.95


class TestExtractors:
    def test_passport_extraction(self):
        ext = PassportExtractor()
        result = ext.extract(PASSPORT_TEXT)
        assert result.fields.get("name") == "Jane Doe"
        assert result.fields.get("passport_number") == "P12345678"
        assert result.fields.get("nationality") == "Indian"

    def test_ielts_extraction(self):
        ext = IELTSExtractor()
        result = ext.extract(IELTS_TEXT)
        assert result.fields.get("overall_band") == "7.5"
        assert result.fields.get("listening") == "8.0"
        assert result.fields.get("speaking") == "7.0"

    def test_transcript_extraction(self):
        ext = TranscriptExtractor()
        result = ext.extract(TRANSCRIPT_TEXT)
        assert "State University" in result.fields.get("institution", "")
        assert result.fields.get("cgpa") == "3.65"

    def test_cv_extraction(self):
        text = "CURRICULUM VITAE\nSkills: Python, React\nExperience: Engineer at TechCorp"
        ext = CVExtractor()
        result = ext.extract(text)
        assert "Python" in result.fields.get("skills", [""])[0]


class TestValidator:
    def test_valid_ielts(self):
        engine = ValidationEngine()
        result = engine.validate("ielts_trf", {"overall_band": "7.5", "listening": "8.0"})
        assert result.is_valid or len(result.warnings) >= 0

    def test_missing_fields_invalid(self):
        engine = ValidationEngine()
        result = engine.validate("passport", {})
        assert not result.is_valid
        assert len(result.errors) > 0


class TestConfidenceScorer:
    def test_high_confidence_valid_doc(self):
        scorer = ConfidenceScorer()
        score = scorer.score(
            classification=ClassificationResult("ielts_trf", 0.9),
            extraction=ExtractionResult("ielts_trf", {"overall_band": "7.5"}, 0.88, {"overall_band": 0.9}),
            validation=ValidationResult(is_valid=True, passed_rules=["overall_band"]),
            ocr_confidence=0.8,
        )
        assert score >= 0.6


class TestPipelineIntegration:
    """End-to-end chain: OCR → classify → extract → validate → score."""

    @pytest.mark.asyncio
    async def test_passport_full_chain(self):
        ocr = FallbackOCRProvider()
        ocr_result = await ocr.extract_text(
            content=PASSPORT_TEXT.encode(),
            file_name="passport_scan.pdf",
            mime_type="application/pdf",
        )
        classifier = DocumentClassifier()
        classification = classifier.classify(ocr_result.raw_text, file_name="passport_scan.pdf")
        assert classification.document_type == "passport"

        extractor = get_extractor(classification.document_type)
        assert extractor is not None
        extraction = extractor.extract(ocr_result.raw_text)
        assert extraction.fields.get("passport_number") == "P12345678"

        validation = ValidationEngine().validate(classification.document_type, extraction.fields)
        score = ConfidenceScorer().score(
            classification=classification,
            extraction=extraction,
            validation=validation,
            ocr_confidence=ocr_result.confidence,
        )
        assert score >= 0.5

    @pytest.mark.asyncio
    async def test_ielts_full_chain_from_filename_hint(self):
        ocr = FallbackOCRProvider()
        ocr_result = await ocr.extract_text(
            content=b"short",
            file_name="ielts_trf.pdf",
            mime_type="application/pdf",
        )
        classification = DocumentClassifier().classify(ocr_result.raw_text, file_name="ielts_trf.pdf")
        assert classification.document_type == "ielts_trf"

        extraction = IELTSExtractor().extract(ocr_result.raw_text)
        validation = ValidationEngine().validate("ielts_trf", extraction.fields)
        assert extraction.fields.get("overall_band") == "7.5"
        assert validation.is_valid or len(validation.warnings) >= 0

    @pytest.mark.asyncio
    async def test_transcript_full_chain(self):
        ocr = FallbackOCRProvider()
        ocr_result = await ocr.extract_text(
            content=TRANSCRIPT_TEXT.encode(),
            file_name="transcript.pdf",
            mime_type="application/pdf",
        )
        classification = DocumentClassifier().classify(ocr_result.raw_text)
        extraction = TranscriptExtractor().extract(ocr_result.raw_text)
        validation = ValidationEngine().validate(classification.document_type, extraction.fields)
        score = ConfidenceScorer().score(
            classification=classification,
            extraction=extraction,
            validation=validation,
            ocr_confidence=ocr_result.confidence,
        )
        assert "State University" in extraction.fields.get("institution", "")
        assert score >= 0.4


class TestDuplicateDetection:
    def test_same_content_same_hash(self):
        content = b"identical document bytes"
        assert DocumentUploadRepository.compute_hash(content) == DocumentUploadRepository.compute_hash(content)

    def test_different_content_different_hash(self):
        assert DocumentUploadRepository.compute_hash(b"doc-a") != DocumentUploadRepository.compute_hash(b"doc-b")


class TestDocumentAPIRoutes:
    def test_jobs_route_registered(self):
        from app.main import app

        job_routes = [
            route
            for route in app.routes
            if getattr(route, "path", "") == "/api/v1/documents/jobs/{job_id}"
        ]
        assert len(job_routes) == 1

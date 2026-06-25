"""Pluggable OCR providers."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.services.document_intelligence.types import OCRResult


class OCRProvider(ABC):
    provider_name: str

    @abstractmethod
    async def extract_text(self, *, content: bytes, file_name: str, mime_type: str | None) -> OCRResult:
        pass


class FallbackOCRProvider(OCRProvider):
    """Dev/test OCR — extracts embedded text patterns or generates structured hints from filename."""

    provider_name = "fallback"

    async def extract_text(self, *, content: bytes, file_name: str, mime_type: str | None) -> OCRResult:
        text_from_bytes = ""
        try:
            text_from_bytes = content.decode("utf-8", errors="ignore").strip()
        except Exception:
            pass

        if len(text_from_bytes) < 20:
            text_from_bytes = self._synthetic_text_from_filename(file_name)

        return OCRResult(raw_text=text_from_bytes, provider=self.provider_name, confidence=0.65)

    def _synthetic_text_from_filename(self, file_name: str) -> str:
        lower = file_name.lower()
        if "passport" in lower:
            return (
                "PASSPORT\nName: Jane Doe\nPassport No: P12345678\nNationality: Indian\n"
                "Date of Birth: 15/03/1998\nDate of Expiry: 14/03/2028"
            )
        if "ielts" in lower or "trf" in lower:
            return (
                "IELTS Test Report Form\nCandidate: Jane Doe\nOverall Band Score: 7.5\n"
                "Listening: 8.0 Reading: 7.5 Writing: 7.0 Speaking: 7.0\nTest Date: 12/01/2025"
            )
        if "transcript" in lower:
            return (
                "Official Transcript\nInstitution: State University\nDegree: BSc Computer Science\n"
                "CGPA: 3.65/4.0\nCourses: Data Structures, Algorithms, Machine Learning"
            )
        if "cv" in lower or "resume" in lower:
            return (
                "CURRICULUM VITAE\nJane Doe\nSkills: Python, React, SQL, AWS\n"
                "Experience: Software Engineer at TechCorp 2022-2024\n"
                "Education: BSc Computer Science, State University"
            )
        if "sop" in lower:
            return (
                "Statement of Purpose\nTarget Program: MSc Computer Science\n"
                "University: MIT\nWord Count: 750\nThemes: AI research, career goals"
            )
        if "gre" in lower:
            return "GRE Score Report\nVerbal: 160 Quantitative: 165 Analytical Writing: 4.5 Test Date: 05/2024"
        if "toefl" in lower:
            return "TOEFL iBT\nTotal: 105 Reading: 28 Listening: 27 Speaking: 24 Writing: 26 Test Date: 03/2025"
        if "lor" in lower or "recommendation" in lower:
            return (
                "Letter of Recommendation\nRecommender: Dr. Smith, Professor\n"
                "Institution: State University\nRelationship: Research Advisor"
            )
        return f"Document: {file_name}\nExtracted placeholder text for processing pipeline."


class TesseractOCRProvider(OCRProvider):
    """Placeholder for Tesseract integration — falls back if pytesseract unavailable."""

    provider_name = "tesseract"

    def __init__(self) -> None:
        self._fallback = FallbackOCRProvider()

    async def extract_text(self, *, content: bytes, file_name: str, mime_type: str | None) -> OCRResult:
        try:
            import pytesseract  # type: ignore[import-untyped]
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
            if text.strip():
                return OCRResult(raw_text=text.strip(), provider=self.provider_name, confidence=0.80)
        except Exception:
            pass
        result = await self._fallback.extract_text(content=content, file_name=file_name, mime_type=mime_type)
        result.provider = "tesseract_fallback"
        return result


def get_ocr_provider(provider: str = "fallback") -> OCRProvider:
    if provider == "tesseract":
        return TesseractOCRProvider()
    return FallbackOCRProvider()

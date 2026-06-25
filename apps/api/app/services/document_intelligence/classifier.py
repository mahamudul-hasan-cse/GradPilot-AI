"""Document classification from OCR text and filename."""

from __future__ import annotations

import re

from app.services.document_intelligence.types import ClassificationResult

CLASSIFICATION_RULES: list[tuple[str, list[str], float]] = [
    ("passport", ["passport", "passport no", "nationality", "date of expiry"], 0.9),
    ("ielts_trf", ["ielts", "test report form", "overall band", "listening", "speaking"], 0.92),
    ("toefl", ["toefl", "ibt", "total score"], 0.88),
    ("gre", ["gre", "verbal reasoning", "quantitative", "analytical writing"], 0.88),
    ("transcript", ["transcript", "cgpa", "gpa", "official transcript", "courses"], 0.85),
    ("degree_certificate", ["degree certificate", "bachelor", "master", "conferred", "graduation"], 0.82),
    ("cv", ["curriculum vitae", "resume", "experience", "skills", "employment"], 0.80),
    ("lor", ["letter of recommendation", "recommender", "reference letter", "lor"], 0.85),
    ("sop", ["statement of purpose", "personal statement", "sop", "motivation letter"], 0.85),
]

FILENAME_HINTS: dict[str, list[str]] = {
    "passport": ["passport"],
    "ielts_trf": ["ielts", "trf"],
    "toefl": ["toefl"],
    "gre": ["gre"],
    "transcript": ["transcript"],
    "degree_certificate": ["degree", "certificate", "diploma"],
    "cv": ["cv", "resume"],
    "lor": ["lor", "recommendation"],
    "sop": ["sop", "statement"],
}


class DocumentClassifier:
    def classify(
        self,
        raw_text: str,
        *,
        file_name: str = "",
        hint_type: str | None = None,
    ) -> ClassificationResult:
        if hint_type and hint_type in {r[0] for r in CLASSIFICATION_RULES}:
            return ClassificationResult(document_type=hint_type, confidence=0.95, signals=["user_hint"])

        text_lower = raw_text.lower()
        file_lower = file_name.lower()
        best_type = "unknown"
        best_score = 0.0
        best_signals: list[str] = []

        for doc_type, keywords, base_conf in CLASSIFICATION_RULES:
            score = 0.0
            signals = []
            for kw in keywords:
                if kw in text_lower:
                    score += 1.0
                    signals.append(f"text:{kw}")
            for hint in FILENAME_HINTS.get(doc_type, []):
                if hint in file_lower:
                    score += 0.5
                    signals.append(f"filename:{hint}")
            if score > best_score:
                best_score = score
                best_type = doc_type
                best_signals = signals

        if best_score == 0:
            return ClassificationResult(document_type="unknown", confidence=0.0, signals=[])

        confidence = min(0.98, 0.5 + best_score * 0.12)
        return ClassificationResult(document_type=best_type, confidence=confidence, signals=best_signals)

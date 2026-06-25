"""Structured field extractors per document type."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.services.document_intelligence.types import ExtractionResult


class FieldExtractor(ABC):
    document_type: str

    @abstractmethod
    def extract(self, raw_text: str) -> ExtractionResult:
        pass


class PassportExtractor(FieldExtractor):
    document_type = "passport"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        if m := re.search(r"Name[:\s]+([^\n]+)", raw_text, re.I):
            fields["name"] = m.group(1).strip()
            conf["name"] = 0.9
        if m := re.search(r"Passport\s+(?:No|Number)[:\s#]*([A-Z0-9]+)", raw_text, re.I):
            fields["passport_number"] = m.group(1).strip()
            conf["passport_number"] = 0.88
        if m := re.search(r"Nationality[:\s]+([^\n]+)", raw_text, re.I):
            fields["nationality"] = m.group(1).strip()
            conf["nationality"] = 0.85
        if m := re.search(r"(?:Expiry|Expiration)[:\s]+(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})", raw_text, re.I):
            fields["expiry_date"] = m.group(1).strip()
            conf["expiry_date"] = 0.87
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("passport", fields, avg, conf)


class TranscriptExtractor(FieldExtractor):
    document_type = "transcript"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        if m := re.search(r"Institution[:\s]+([^\n]+)", raw_text, re.I):
            fields["institution"] = m.group(1).strip()
            conf["institution"] = 0.88
        if m := re.search(r"Degree[:\s]+([^\n]+)", raw_text, re.I):
            fields["degree"] = m.group(1).strip()
            conf["degree"] = 0.85
        if m := re.search(r"CGPA[:\s]+([\d.]+)", raw_text, re.I):
            fields["cgpa"] = m.group(1).strip()
            conf["cgpa"] = 0.90
        courses_match = re.search(r"Courses[:\s]+([^\n]+)", raw_text, re.I)
        if courses_match:
            fields["courses"] = [c.strip() for c in courses_match.group(1).split(",")]
            conf["courses"] = 0.80
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("transcript", fields, avg, conf)


class IELTSExtractor(FieldExtractor):
    document_type = "ielts_trf"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        patterns = {
            "overall_band": r"Overall\s+Band(?:\s+Score)?[:\s]+([\d.]+)",
            "listening": r"Listening[:\s]+([\d.]+)",
            "reading": r"Reading[:\s]+([\d.]+)",
            "writing": r"Writing[:\s]+([\d.]+)",
            "speaking": r"Speaking[:\s]+([\d.]+)",
            "test_date": r"Test\s+Date[:\s]+([\d/\-]+)",
            "candidate_name": r"Candidate[:\s]+([A-Za-z\s]+)",
        }
        for key, pattern in patterns.items():
            if m := re.search(pattern, raw_text, re.I):
                fields[key] = m.group(1).strip()
                conf[key] = 0.88
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("ielts_trf", fields, avg, conf)


class CVExtractor(FieldExtractor):
    document_type = "cv"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {"skills": [], "experience": [], "projects": [], "education": []}
        conf: dict[str, float] = {}
        if m := re.search(r"Skills[:\s]+([^\n]+)", raw_text, re.I):
            fields["skills"] = [s.strip() for s in re.split(r"[,;]", m.group(1)) if s.strip()]
            conf["skills"] = 0.82
        if m := re.search(r"Experience[:\s]+([^\n]+)", raw_text, re.I):
            fields["experience"] = [m.group(1).strip()]
            conf["experience"] = 0.80
        if m := re.search(r"Education[:\s]+([^\n]+)", raw_text, re.I):
            fields["education"] = [m.group(1).strip()]
            conf["education"] = 0.80
        if m := re.search(r"Projects[:\s]+([^\n]+)", raw_text, re.I):
            fields["projects"] = [m.group(1).strip()]
            conf["projects"] = 0.75
        avg = sum(conf.values()) / len(conf) if conf else 0.35
        return ExtractionResult("cv", fields, avg, conf)


class TOEFLExtractor(FieldExtractor):
    document_type = "toefl"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        for key, pattern in {
            "total_score": r"Total[:\s]+(\d+)",
            "reading": r"Reading[:\s]+(\d+)",
            "listening": r"Listening[:\s]+(\d+)",
            "speaking": r"Speaking[:\s]+(\d+)",
            "writing": r"Writing[:\s]+(\d+)",
            "test_date": r"Test\s+Date[:\s]+([\d/\-]+)",
        }.items():
            if m := re.search(pattern, raw_text, re.I):
                fields[key] = m.group(1).strip()
                conf[key] = 0.85
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("toefl", fields, avg, conf)


class GREExtractor(FieldExtractor):
    document_type = "gre"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        for key, pattern in {
            "verbal": r"Verbal[:\s]+(\d+)",
            "quantitative": r"Quantitative[:\s]+(\d+)",
            "analytical_writing": r"Analytical\s+Writing[:\s]+([\d.]+)",
            "test_date": r"Test\s+Date[:\s]+([\d/\-]+)",
        }.items():
            if m := re.search(pattern, raw_text, re.I):
                fields[key] = m.group(1).strip()
                conf[key] = 0.85
        if "verbal" in fields and "quantitative" in fields:
            fields["total"] = str(int(fields["verbal"]) + int(fields["quantitative"]))
            conf["total"] = 0.80
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("gre", fields, avg, conf)


class LORExtractor(FieldExtractor):
    document_type = "lor"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        if m := re.search(r"Recommender[:\s]+([^\n,]+)", raw_text, re.I):
            fields["recommender_name"] = m.group(1).strip()
            conf["recommender_name"] = 0.85
        if m := re.search(r"Institution[:\s]+([^\n]+)", raw_text, re.I):
            fields["institution"] = m.group(1).strip()
            conf["institution"] = 0.82
        if m := re.search(r"Relationship[:\s]+([^\n]+)", raw_text, re.I):
            fields["relationship"] = m.group(1).strip()
            conf["relationship"] = 0.80
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("lor", fields, avg, conf)


class SOPExtractor(FieldExtractor):
    document_type = "sop"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        if m := re.search(r"Target\s+Program[:\s]+([^\n]+)", raw_text, re.I):
            fields["target_program"] = m.group(1).strip()
            conf["target_program"] = 0.82
        if m := re.search(r"University[:\s]+([^\n]+)", raw_text, re.I):
            fields["university"] = m.group(1).strip()
            conf["university"] = 0.80
        if m := re.search(r"Word\s+Count[:\s]+(\d+)", raw_text, re.I):
            fields["word_count"] = int(m.group(1))
            conf["word_count"] = 0.90
        fields["title"] = "Statement of Purpose"
        fields["themes"] = []
        if "research" in raw_text.lower():
            fields["themes"].append("research")
        if "career" in raw_text.lower():
            fields["themes"].append("career")
        conf["title"] = 0.95
        avg = sum(conf.values()) / len(conf) if conf else 0.4
        return ExtractionResult("sop", fields, avg, conf)


class DegreeCertificateExtractor(FieldExtractor):
    document_type = "degree_certificate"

    def extract(self, raw_text: str) -> ExtractionResult:
        fields: dict = {}
        conf: dict[str, float] = {}
        if m := re.search(r"Institution[:\s]+([^\n]+)", raw_text, re.I):
            fields["institution"] = m.group(1).strip()
            conf["institution"] = 0.85
        if m := re.search(r"(BSc|MSc|BA|MA|Bachelor|Master|PhD)[^\n]*", raw_text, re.I):
            fields["degree"] = m.group(0).strip()
            conf["degree"] = 0.82
        avg = sum(conf.values()) / len(conf) if conf else 0.3
        return ExtractionResult("degree_certificate", fields, avg, conf)


EXTRACTOR_REGISTRY: dict[str, FieldExtractor] = {
    "passport": PassportExtractor(),
    "transcript": TranscriptExtractor(),
    "ielts_trf": IELTSExtractor(),
    "cv": CVExtractor(),
    "toefl": TOEFLExtractor(),
    "gre": GREExtractor(),
    "lor": LORExtractor(),
    "sop": SOPExtractor(),
    "degree_certificate": DegreeCertificateExtractor(),
}


def get_extractor(document_type: str) -> FieldExtractor | None:
    return EXTRACTOR_REGISTRY.get(document_type)

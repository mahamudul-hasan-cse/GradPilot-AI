"""Document validation engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.document_intelligence.types import EXTRACTION_SCHEMAS, ValidationResult


class ValidationEngine:
    def validate(self, document_type: str, fields: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        passed: list[str] = []
        required = EXTRACTION_SCHEMAS.get(document_type, [])

        for field in required:
            if field not in fields or fields[field] in (None, "", []):
                errors.append(f"Missing required field: {field}")
            else:
                passed.append(field)

        if document_type == "passport":
            self._validate_passport(fields, errors, warnings, passed)
        elif document_type == "ielts_trf":
            self._validate_ielts(fields, errors, warnings, passed)
        elif document_type == "transcript":
            self._validate_transcript(fields, errors, warnings, passed)
        elif document_type == "cv":
            if not fields.get("skills") and not fields.get("experience"):
                warnings.append("CV has limited extractable content")

        is_valid = len(errors) == 0 and len(passed) > 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings, passed_rules=passed)

    def _validate_passport(self, fields: dict, errors: list, warnings: list, passed: list) -> None:
        expiry = fields.get("expiry_date")
        if expiry:
            try:
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
                    try:
                        exp_date = datetime.strptime(expiry, fmt).date()
                        if exp_date < datetime.now().date():
                            warnings.append("Passport appears expired")
                        else:
                            passed.append("expiry_valid")
                        break
                    except ValueError:
                        continue
            except Exception:
                warnings.append("Could not parse expiry date")

    def _validate_ielts(self, fields: dict, errors: list, warnings: list, passed: list) -> None:
        overall = fields.get("overall_band")
        if overall:
            try:
                band = float(overall)
                if band < 0 or band > 9:
                    errors.append("IELTS overall band out of range (0-9)")
                elif band < 5.5:
                    warnings.append("IELTS band below typical university minimum (5.5)")
                else:
                    passed.append("ielts_band_valid")
            except ValueError:
                errors.append("Invalid IELTS overall band format")

    def _validate_transcript(self, fields: dict, errors: list, warnings: list, passed: list) -> None:
        cgpa = fields.get("cgpa")
        if cgpa:
            try:
                gpa = float(str(cgpa).split("/")[0])
                if gpa > 4.0:
                    warnings.append("CGPA may be on a scale other than 4.0")
                passed.append("cgpa_parsed")
            except ValueError:
                errors.append("Invalid CGPA format")

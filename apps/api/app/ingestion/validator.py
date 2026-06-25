"""Data quality validation for ingested university records."""

from __future__ import annotations

from app.ingestion.schemas import NormalizedUniversityData, ValidationIssue, ValidationReport

REQUIRED_FIELDS = ("name", "country", "website", "source_url")
IMPORTANT_FIELDS = (
    "tuition_fee",
    "minimum_gpa",
    "minimum_ielts",
    "deadline",
    "programs",
    "description",
)


class DataQualityValidator:
    def validate(self, data: NormalizedUniversityData) -> ValidationReport:
        issues: list[ValidationIssue] = []
        fields_present = 0

        for field in REQUIRED_FIELDS:
            value = getattr(data, field, None)
            if value:
                fields_present += 1
            else:
                issues.append(ValidationIssue(
                    field=field, severity="error", message=f"Required field '{field}' is missing"
                ))

        for field in IMPORTANT_FIELDS:
            value = getattr(data, field, None)
            if value:
                fields_present += 1
            else:
                issues.append(ValidationIssue(
                    field=field, severity="warning", message=f"Recommended field '{field}' is missing"
                ))

        if data.tuition_fee is not None and data.tuition_fee < 0:
            issues.append(ValidationIssue(field="tuition_fee", severity="error", message="Tuition cannot be negative"))

        if data.minimum_gpa is not None and (data.minimum_gpa < 0 or data.minimum_gpa > 4):
            issues.append(ValidationIssue(field="minimum_gpa", severity="warning", message="GPA outside 0-4 range"))

        if data.minimum_ielts is not None and (data.minimum_ielts < 0 or data.minimum_ielts > 9):
            issues.append(ValidationIssue(field="minimum_ielts", severity="warning", message="IELTS outside 0-9 range"))

        if not data.programs:
            issues.append(ValidationIssue(field="programs", severity="warning", message="No programs extracted"))

        total_fields = len(REQUIRED_FIELDS) + len(IMPORTANT_FIELDS)
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")

        score = max(0.0, 100.0 - (error_count * 25) - (warning_count * 5))
        coverage_bonus = (fields_present / total_fields) * 20
        score = min(100.0, score * 0.8 + coverage_bonus)

        return ValidationReport(
            score=round(score, 2),
            passed=error_count == 0 and score >= 50,
            issues=issues,
            fields_present=fields_present,
            fields_required=len(REQUIRED_FIELDS),
        )

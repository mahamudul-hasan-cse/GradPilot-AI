"""Tests for SOP Studio."""

import pytest

from app.schemas.sop_studio import SOPGrammarRequest
from app.services.sop_studio.export_engine import SOPExportEngine
from app.services.sop_studio.grammar_engine import SOPGrammarEngine
from app.services.sop_studio.plagiarism import SOPPlagiarismService
from app.services.sop_studio.scoring_engine import SOPScoringEngine
from app.services.sop_studio.utils import (
    count_words,
    diff_summary,
    html_to_plain,
    plain_to_html,
    text_similarity,
)
from app.services.digital_twin.types import TwinEventType


SAMPLE_SOP = (
    "From my undergraduate research in distributed systems, I developed a passion for "
    "building reliable infrastructure. At State University, I led a team that reduced "
    "deployment latency by 40%. I am applying to the MS Computer Science program at "
    "Example University to work with Dr. Smith on cloud-native systems. My career goal "
    "is to contribute to open-source platforms that power global education."
)


class TestUtils:
    def test_count_words(self):
        assert count_words("one two three") == 3
        assert count_words("") == 0

    def test_plain_html_roundtrip(self):
        plain = "First paragraph.\n\nSecond paragraph."
        html = plain_to_html(plain)
        assert "<p>" in html
        assert html_to_plain(html) == plain

    def test_text_similarity_identical(self):
        assert text_similarity("hello world", "hello world") == 100.0

    def test_diff_summary(self):
        summary = diff_summary("short text", "short text with more words added")
        assert "similar" in summary.lower()


class TestScoringEngine:
    def test_scores_well_structured_sop(self):
        engine = SOPScoringEngine()
        content = "\n\n".join([SAMPLE_SOP] * 4)
        result = engine.score(content, target_word_count=200)
        assert result.overall >= 50
        assert result.clarity > 0
        assert result.reasons.get("overall")

    def test_short_sop_feedback(self):
        engine = SOPScoringEngine()
        result = engine.score("Brief essay.", target_word_count=750)
        assert any("short" in f.lower() for f in result.feedback)


class TestGrammarEngine:
    @pytest.mark.asyncio
    async def test_fixes_capital_i(self):
        engine = SOPGrammarEngine()
        corrected, issues = await engine.review("i am passionate about research.")
        assert "I" in corrected or len(issues) > 0

    @pytest.mark.asyncio
    async def test_grammar_response_shape(self):
        engine = SOPGrammarEngine()
        corrected, issues = await engine.review(SAMPLE_SOP)
        req = SOPGrammarRequest(content_plain=SAMPLE_SOP)
        assert req.content_plain == SAMPLE_SOP
        assert isinstance(corrected, str)
        assert isinstance(issues, list)


class TestExportEngine:
    def test_export_markdown(self):
        engine = SOPExportEngine()
        data, filename, mime = engine.export_markdown(title="My SOP", content_plain=SAMPLE_SOP)
        assert filename.endswith(".md")
        assert mime == "text/markdown"
        assert b"My SOP" in data

    def test_export_docx(self):
        engine = SOPExportEngine()
        data, filename, mime = engine.export_docx(title="My SOP", content_plain=SAMPLE_SOP)
        assert filename.endswith(".docx")
        assert len(data) > 0

    def test_export_pdf(self):
        engine = SOPExportEngine()
        data, filename, mime = engine.export_pdf(title="My SOP", content_plain=SAMPLE_SOP)
        assert filename.endswith(".pdf")
        assert data[:4] == b"%PDF"

    def test_base64_encoding(self):
        engine = SOPExportEngine()
        encoded = engine.to_base64(b"test")
        assert encoded == "dGVzdA=="


class TestPlagiarismPlaceholder:
    @pytest.mark.asyncio
    async def test_placeholder_response(self):
        service = SOPPlagiarismService()
        result = await service.check(content=SAMPLE_SOP, document_id="doc-123")
        assert result["status"] == "placeholder"
        assert result["report_available"] is False
        assert result["check_id"]


class TestTwinEventTypes:
    def test_sop_events_defined(self):
        assert TwinEventType.SOP_CREATED == "sop.created"
        assert TwinEventType.SOP_UPDATED == "sop.updated"
        assert TwinEventType.SOP_EXPORTED == "sop.exported"
        assert TwinEventType.SOP_SCORED == "sop.scored"

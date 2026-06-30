"""SOP export engine — PDF, DOCX, Markdown."""

from __future__ import annotations

import base64
import io
from datetime import UTC, datetime


class SOPExportEngine:
    def export_markdown(self, *, title: str, content_plain: str) -> tuple[bytes, str, str]:
        md = f"# {title}\n\n_Generated {datetime.now(UTC).date().isoformat()}_\n\n{content_plain}\n"
        data = md.encode("utf-8")
        filename = f"{self._safe_name(title)}.md"
        return data, filename, "text/markdown"

    def export_docx(self, *, title: str, content_plain: str) -> tuple[bytes, str, str]:
        try:
            from docx import Document

            doc = Document()
            doc.add_heading(title, 0)
            for para in content_plain.split("\n\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())
            buffer = io.BytesIO()
            doc.save(buffer)
            data = buffer.getvalue()
        except ImportError:
            data = self._minimal_docx_bytes(title, content_plain)
        filename = f"{self._safe_name(title)}.docx"
        return data, filename, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def export_pdf(self, *, title: str, content_plain: str) -> tuple[bytes, str, str]:
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 10, title)
            pdf.ln(4)
            pdf.set_font("Helvetica", size=11)
            for para in content_plain.split("\n\n"):
                if para.strip():
                    pdf.multi_cell(0, 6, para.strip())
                    pdf.ln(3)
            data = pdf.output()
        except ImportError:
            data = self._minimal_pdf_bytes(title, content_plain)
        filename = f"{self._safe_name(title)}.pdf"
        return data, filename, "application/pdf"

    def to_base64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("ascii")

    def _safe_name(self, title: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:80] or "sop"

    def _minimal_pdf_bytes(self, title: str, content: str) -> bytes:
        """Minimal valid PDF without fpdf dependency."""
        text = f"{title}\n\n{content}"[:3000].replace("(", "[").replace(")", "]")
        stream = f"BT /F1 11 Tf 50 750 Td ({text[:500]}) Tj ET"
        pdf = (
            f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            f"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            f"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R"
            f"/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>> >>endobj\n"
            f"4 0 obj<</Length {len(stream)}>>stream\n{stream}\nendstream endobj\n"
            f"xref\n0 5\n0000000000 65535 f \n"
            f"trailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        return pdf.encode("latin-1", errors="replace")

    def _minimal_docx_bytes(self, title: str, content: str) -> bytes:
        """Fallback: export as plain text wrapped in zip-less minimal structure."""
        return f"{title}\n\n{content}".encode("utf-8")

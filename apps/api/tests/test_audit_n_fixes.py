"""Regression tests for the post-C1–C7 audit findings (N1–N3, CORS, upload storage)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import Settings, is_loopback_origin
from app.repositories.university import tokenize_search_query
from app.services.application_workspace.workspace_service import ApplicationWorkspaceService
from app.services.document_intelligence.service import DocumentIntelligenceService
from app.services.document_intelligence.storage import LocalUploadStorage


class TestSearchTokenizer:
    def test_multi_word_query_splits_into_tokens(self):
        assert tokenize_search_query("computer science Germany") == ["computer", "science", "germany"]

    def test_drops_stopwords_duplicates_and_short_tokens(self):
        assert tokenize_search_query("The best universities in Germany for x germany") == ["germany"]

    def test_expands_country_aliases(self):
        assert tokenize_search_query("data science UK") == ["data", "science", "united kingdom"]

    def test_only_stopwords_yields_no_tokens(self):
        assert tokenize_search_query("top universities") == []


class TestCorsOrigins:
    ORIGINS = "https://gradpilot-ai.vercel.app,http://localhost:3000,http://127.0.0.1:3000"

    def test_production_drops_loopback_origins(self):
        s = Settings(ENVIRONMENT="production", CORS_ORIGINS=self.ORIGINS)
        assert s.cors_origins_list == ["https://gradpilot-ai.vercel.app"]

    def test_development_keeps_loopback_origins(self):
        s = Settings(ENVIRONMENT="development", CORS_ORIGINS=self.ORIGINS)
        assert s.cors_origins_list == self.ORIGINS.split(",")

    @pytest.mark.parametrize(
        ("origin", "expected"),
        [
            ("http://localhost:3000", True),
            ("http://127.0.0.1:3000", True),
            ("http://app.localhost", True),
            ("https://gradpilot-ai.vercel.app", False),
            ("https://localhost.example.com", False),
        ],
    )
    def test_is_loopback_origin(self, origin, expected):
        assert is_loopback_origin(origin) is expected


class TestLocalUploadStorage:
    def test_round_trip(self, tmp_path):
        storage = LocalUploadStorage(tmp_path)
        url = storage.save("abc_cv.txt", b"hello")
        assert url == "/uploads/abc_cv.txt"
        assert storage.load(url) == b"hello"

    @pytest.mark.parametrize("name", ["../evil.txt", "sub/evil.txt", "..", ""])
    def test_rejects_names_outside_base_dir(self, tmp_path, name):
        storage = LocalUploadStorage(tmp_path / "uploads")
        with pytest.raises(HTTPException):
            storage.save(name, b"x")
        assert not (tmp_path / "evil.txt").exists()

    def test_load_refuses_traversal(self, tmp_path):
        (tmp_path / "secret.txt").write_bytes(b"secret")
        storage = LocalUploadStorage(tmp_path / "uploads")
        assert storage.load("/uploads/../secret.txt") is None
        assert storage.load("https://example.com/x") is None


def _doc_service(doc) -> DocumentIntelligenceService:
    service = DocumentIntelligenceService.__new__(DocumentIntelligenceService)
    service.doc_repo = SimpleNamespace(get_for_user=AsyncMock(return_value=doc), update=AsyncMock())
    return service


class TestValidateDocumentErrors:
    async def test_parsed_without_fields_reports_missing_fields(self):
        doc = SimpleNamespace(status="parsed", extracted_fields={}, classified_type="cv")
        with pytest.raises(HTTPException) as exc:
            await _doc_service(doc).validate_document(SimpleNamespace(id=uuid4()), uuid4())
        assert exc.value.status_code == 422
        assert "no fields could be extracted" in exc.value.detail

    async def test_still_processing_reports_not_parsed(self):
        doc = SimpleNamespace(status="processing", extracted_fields=None, classified_type=None)
        with pytest.raises(HTTPException) as exc:
            await _doc_service(doc).validate_document(SimpleNamespace(id=uuid4()), uuid4())
        assert exc.value.status_code == 400
        assert "not yet parsed" in exc.value.detail

    async def test_failed_parse_is_reported(self):
        doc = SimpleNamespace(status="failed", extracted_fields=None, classified_type=None)
        with pytest.raises(HTTPException) as exc:
            await _doc_service(doc).validate_document(SimpleNamespace(id=uuid4()), uuid4())
        assert exc.value.status_code == 422


class TestApplicationReferenceValidation:
    async def test_unknown_university_is_404(self):
        db = SimpleNamespace(get=AsyncMock(return_value=None))
        service = ApplicationWorkspaceService.__new__(ApplicationWorkspaceService)
        service.db = db
        with pytest.raises(HTTPException) as exc:
            await service._ensure_references_exist(university_id=uuid4())
        assert exc.value.status_code == 404
        assert exc.value.detail == "University not found"

    async def test_missing_ids_skip_lookup(self):
        db = SimpleNamespace(get=AsyncMock())
        service = ApplicationWorkspaceService.__new__(ApplicationWorkspaceService)
        service.db = db
        await service._ensure_references_exist()
        db.get.assert_not_called()

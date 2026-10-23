"""Storage backends for uploaded document bytes.

Only the local-disk backend exists today. On App Service with
WEBSITES_ENABLE_APP_SERVICE_STORAGE=false that disk is ephemeral: files are
lost on restart, redeploy or scale-out while DB rows keep pointing at them.

TODO(blob): implement an Azure Blob backend behind UPLOAD_BACKEND=blob
(azure-storage-blob, a container plus connection string or managed identity).
Until then ``blob`` logs a warning and falls back to local disk so uploads keep
working.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_URL_PREFIX = "/uploads/"


class LocalUploadStorage:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, name: str) -> Path:
        # Names are already sanitized, but never let a write or read escape base_dir.
        path = (self.base_dir / name).resolve()
        if path.parent != self.base_dir:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")
        return path

    def save(self, name: str, content: bytes) -> str:
        """Store ``content`` under ``name`` and return its public file_url."""
        self._resolve(name).write_bytes(content)
        return f"{UPLOAD_URL_PREFIX}{name}"

    def load(self, file_url: str | None) -> bytes | None:
        if not file_url or not file_url.startswith(UPLOAD_URL_PREFIX):
            return None
        try:
            path = self._resolve(file_url[len(UPLOAD_URL_PREFIX) :])
        except HTTPException:
            logger.warning("Refusing to read upload outside storage dir: %s", file_url)
            return None
        return path.read_bytes() if path.exists() else None


_warned_blob_fallback = False


def get_upload_storage() -> LocalUploadStorage:
    global _warned_blob_fallback
    if settings.upload_backend == "blob" and not _warned_blob_fallback:
        logger.warning("UPLOAD_BACKEND=blob is not implemented yet; storing uploads on local disk")
        _warned_blob_fallback = True
    return LocalUploadStorage(settings.document_upload_dir)

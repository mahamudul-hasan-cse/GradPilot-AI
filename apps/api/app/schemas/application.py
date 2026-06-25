"""Backward-compatible re-exports — use application_workspace schemas."""

from app.schemas.application_workspace import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)

__all__ = ["ApplicationCreate", "ApplicationResponse", "ApplicationUpdate"]

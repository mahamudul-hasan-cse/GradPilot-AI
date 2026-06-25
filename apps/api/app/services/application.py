"""Backward-compatible wrapper — use ApplicationWorkspaceService."""

from app.services.application_workspace.workspace_service import ApplicationWorkspaceService as ApplicationService

__all__ = ["ApplicationService"]

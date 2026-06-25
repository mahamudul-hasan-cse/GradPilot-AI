from datetime import date, datetime
from uuid import uuid4

import pytest

from app.models.application import Application
from app.services.application_workspace.constants import AUTO_TASK_TEMPLATES, PROGRESS_WEIGHTS
from app.services.application_workspace.deadline_engine import DeadlineEngine
from app.services.application_workspace.progress_engine import ProgressEngine
from app.services.application_workspace.task_engine import TaskEngine


def _application(**kwargs) -> Application:
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "status": "planning",
        "profile_complete": True,
        "documents_complete": False,
        "sop_complete": False,
        "lor_complete": False,
        "submitted_complete": False,
        "documents": [],
        "tasks": [],
        "deadlines": [],
    }
    defaults.update(kwargs)
    return Application(**defaults)


class TestProgressWeights:
    def test_weights_sum_to_100(self):
        assert sum(PROGRESS_WEIGHTS.values()) == 100


class TestProgressEngine:
    def test_zero_progress_by_default(self):
        engine = ProgressEngine()
        app = _application()
        result = engine.calculate(app)
        assert result["progress_percent"] == 20  # profile only

    def test_full_progress(self):
        engine = ProgressEngine()
        app = _application(
            profile_complete=True,
            documents_complete=True,
            sop_complete=True,
            lor_complete=True,
            submitted_complete=True,
        )
        result = engine.calculate(app)
        assert result["progress_percent"] == 100.0

    def test_sync_from_documents(self):
        from app.models.application import ApplicationDocument

        engine = ProgressEngine()
        app = _application(
            documents=[
                ApplicationDocument(
                    id=uuid4(),
                    application_id=uuid4(),
                    document_type="transcript",
                    title="Transcript",
                    status="uploaded",
                    file_url="https://example.com/t.pdf",
                ),
                ApplicationDocument(
                    id=uuid4(),
                    application_id=uuid4(),
                    document_type="sop",
                    title="SOP",
                    status="uploaded",
                    file_url="https://example.com/sop.pdf",
                ),
            ]
        )
        engine.sync_flags_from_documents(app)
        assert app.sop_complete is True
        assert app.documents_complete is True

    def test_submitted_status_sets_flag(self):
        engine = ProgressEngine()
        app = _application(status="submitted")
        engine.sync_submitted_flag(app)
        assert app.submitted_complete is True


class TestTaskTemplates:
    def test_has_required_tasks(self):
        types = {t["task_type"] for t in AUTO_TASK_TEMPLATES}
        assert "upload_transcript" in types
        assert "generate_sop" in types
        assert "request_lor" in types
        assert "submit_application" in types
        assert "visa_application" in types


class TestDeadlineEngine:
    def test_should_send_reminder(self):
        from app.models.application import ApplicationDeadline

        engine = DeadlineEngine(db=None)  # type: ignore[arg-type]
        deadline = ApplicationDeadline(
            id=uuid4(),
            application_id=uuid4(),
            deadline_type="application",
            title="App Deadline",
            due_date=date(2026, 12, 1),
            reminder_days_before=14,
            is_completed=False,
        )
        assert engine.should_send_reminder(deadline, today=date(2026, 11, 20)) is True
        assert engine.should_send_reminder(deadline, today=date(2026, 10, 1)) is False

    def test_completed_deadline_no_reminder(self):
        from app.models.application import ApplicationDeadline

        engine = DeadlineEngine(db=None)  # type: ignore[arg-type]
        deadline = ApplicationDeadline(
            id=uuid4(),
            application_id=uuid4(),
            deadline_type="application",
            title="App Deadline",
            due_date=date(2026, 12, 1),
            reminder_days_before=14,
            is_completed=True,
        )
        assert engine.should_send_reminder(deadline, today=date(2026, 11, 20)) is False

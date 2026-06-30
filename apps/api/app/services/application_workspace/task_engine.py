"""Intelligent task generation for applications."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationTask
from app.repositories.application_task import ApplicationTaskRepository
from app.services.application_workspace.constants import AUTO_TASK_TEMPLATES


class TaskEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = ApplicationTaskRepository(db)

    async def generate_tasks(
        self,
        application: Application,
        *,
        due_date: date | None = None,
    ) -> list[ApplicationTask]:
        existing_tasks = await self.task_repo.get_by_application(application.id)
        existing_types = {t.task_type for t in existing_tasks}
        created: list[ApplicationTask] = []

        for template in AUTO_TASK_TEMPLATES:
            if template["task_type"] in existing_types:
                continue
            task = ApplicationTask(
                application_id=application.id,
                title=template["title"],
                description=template["description"],
                task_type=template["task_type"],
                status="pending",
                priority=template["priority"],
                due_date=due_date or application.deadline,
                is_auto_generated=True,
                sort_order=template["sort_order"],
            )
            created.append(await self.task_repo.create(task))

        return created

    async def complete_task(self, task: ApplicationTask) -> ApplicationTask:
        from datetime import UTC, datetime

        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        return await self.task_repo.update(task)

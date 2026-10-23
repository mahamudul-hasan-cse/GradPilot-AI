from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Application)

    def _workspace_options(self):
        return (
            selectinload(Application.program),
            selectinload(Application.university),
            selectinload(Application.scholarship),
            selectinload(Application.documents),
            selectinload(Application.tasks),
            selectinload(Application.workspace_notes),
            selectinload(Application.activity),
            selectinload(Application.deadlines),
        )

    async def get_by_user_id(
        self,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .options(*self._workspace_options())
            .where(Application.user_id == user_id)
            .order_by(Application.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, entity: Application) -> Application:
        # A plain refresh() expires lazy relationships, and reading them later
        # (e.g. ApplicationResponse.university) would lazy-load outside the
        # async greenlet (MissingGreenlet). Refresh columns only.
        await self.db.flush()
        column_keys = [attr.key for attr in inspect(Application).column_attrs]
        await self.db.refresh(entity, attribute_names=column_keys)
        return entity

    async def get_by_id_for_user(
        self,
        application_id: UUID,
        user_id: UUID,
        *,
        populate_existing: bool = False,
    ) -> Application | None:
        stmt = (
            select(Application)
            .options(*self._workspace_options())
            .where(Application.id == application_id, Application.user_id == user_id)
        )
        if populate_existing:
            # Reload relationships on an instance already in the identity map,
            # e.g. after its foreign keys changed.
            stmt = stmt.execution_options(populate_existing=True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_workspace(self, application_id: UUID, user_id: UUID) -> Application | None:
        return await self.get_by_id_for_user(application_id, user_id)

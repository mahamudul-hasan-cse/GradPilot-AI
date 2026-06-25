from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: AsyncSession, model: type[ModelT]):
        self.db = db
        self.model = model

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        return await self.db.get(self.model, entity_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelT]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.db.delete(entity)
        await self.db.flush()

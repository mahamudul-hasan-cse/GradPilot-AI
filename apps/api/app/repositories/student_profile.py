from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_profile import StudentProfile
from app.repositories.base import BaseRepository


class StudentProfileRepository(BaseRepository[StudentProfile]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudentProfile)

    async def get_by_user_id(self, user_id: UUID) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

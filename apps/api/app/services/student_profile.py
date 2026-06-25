from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_profile import StudentProfile
from app.models.user import User
from app.repositories.student_profile import StudentProfileRepository
from app.schemas.student_profile import (
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)


class StudentProfileService:
    def __init__(self, db: AsyncSession):
        self.profile_repo = StudentProfileRepository(db)

    async def get_profile(self, user: User) -> StudentProfileResponse:
        profile = await self.profile_repo.get_by_user_id(user.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return StudentProfileResponse.model_validate(profile)

    async def create_profile(
        self, user: User, data: StudentProfileCreate
    ) -> StudentProfileResponse:
        existing = await self.profile_repo.get_by_user_id(user.id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile already exists. Use PUT to update.",
            )

        profile = StudentProfile(user_id=user.id, **data.model_dump())
        created = await self.profile_repo.create(profile)
        return StudentProfileResponse.model_validate(created)

    async def update_profile(
        self, user: User, data: StudentProfileUpdate
    ) -> StudentProfileResponse:
        profile = await self.profile_repo.get_by_user_id(user.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        updated = await self.profile_repo.update(profile)
        return StudentProfileResponse.model_validate(updated)

    async def upsert_profile(
        self, user: User, data: StudentProfileUpdate
    ) -> StudentProfileResponse:
        profile = await self.profile_repo.get_by_user_id(user.id)
        if profile is None:
            return await self.create_profile(user, StudentProfileCreate(**data.model_dump()))
        return await self.update_profile(user, data)

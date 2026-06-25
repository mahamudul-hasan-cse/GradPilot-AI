from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RefreshTokenRequest, TokenResponse, UserLogin, UserRegister, UserResponse
from app.schemas.common import MessageResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)) -> UserResponse:
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = AuthService(db)
    return await service.get_current_user_profile(current_user)


@router.post("/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    # Stateless JWT — client discards tokens; endpoint provided for API symmetry.
    return MessageResponse(message="Successfully logged out")

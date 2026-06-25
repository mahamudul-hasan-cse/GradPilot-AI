from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: UUID | str, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta
    payload = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: UUID | str, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    expire = datetime.now(UTC) + expires_delta
    payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def _verify_token(token: str, expected_type: str) -> UUID:
    try:
        payload = decode_token(token)
        if payload.get("type") != expected_type:
            raise JWTError("Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError("Missing subject")
        return UUID(user_id)
    except (JWTError, ValueError) as exc:
        raise JWTError("Could not validate credentials") from exc


def verify_access_token(token: str) -> UUID:
    return _verify_token(token, "access")


def verify_refresh_token(token: str) -> UUID:
    return _verify_token(token, "refresh")

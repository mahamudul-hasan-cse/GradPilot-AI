from uuid import uuid4

import pytest
from jose import JWTError

from app.core.config import settings
from app.core.security import create_access_token, verify_access_token


def test_jwt_secret_is_loaded_from_effective_secret():
    assert settings.effective_jwt_secret
    assert settings.effective_jwt_secret in {settings.secret_key, settings.jwt_secret_key}


def test_access_token_round_trip():
    user_id = uuid4()
    token = create_access_token(user_id)

    assert verify_access_token(token) == user_id


def test_invalid_access_token_is_rejected():
    with pytest.raises(JWTError):
        verify_access_token("not-a-valid-token")

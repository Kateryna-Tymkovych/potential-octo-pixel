import pytest
import jwt
from datetime import timedelta
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_jwt_tokens():
    data = {"sub": "user@example.com", "role": "user"}
    access_token = create_access_token(data)
    assert isinstance(access_token, str)

    decoded = decode_token(access_token)
    assert decoded["sub"] == "user@example.com"
    assert decoded["role"] == "user"
    assert "exp" in decoded

    refresh_token = create_refresh_token(data)
    assert isinstance(refresh_token, str)
    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == "user@example.com"

def test_decode_invalid_token():
    with pytest.raises(jwt.InvalidTokenError):
        decode_token("invalid.token.here")

def test_decode_expired_token():
    data = {"sub": "expired@example.com"}
    expired_token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)

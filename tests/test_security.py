from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    password = "secretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_tokens():
    data = {"sub": "test@example.com", "role": "admin"}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == data["sub"]
    assert decoded["role"] == data["role"]
    assert decoded["type"] == "access"

def test_invalid_jwt():
    assert decode_token("invalid-token") == {}

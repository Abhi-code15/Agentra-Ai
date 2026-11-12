"""Unit tests for cryptographic functions: Argon2id, JWT, and token hashing."""
from datetime import timedelta
import pytest
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    """Verifies that Argon2id hashes passwords securely and verifies correctly."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    # Hash should not be plaintext
    assert hashed != password
    assert hashed.startswith("$argon2id$")

    # Correct password verifies
    assert verify_password(password, hashed) is True

    # Incorrect password fails
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_access_token_lifecycle() -> None:
    """Verifies JWT access token minting and payload decoding."""
    user_id = "8f8b8e88-6ef8-490b-b183-b78912ef0011"
    role = "USER"
    token = create_access_token(subject=user_id, role=role)

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert "jti" in payload
    assert "exp" in payload


def test_jwt_expired_token_raises_unauthorized() -> None:
    """Verifies that decoding an expired JWT raises UnauthorizedException."""
    user_id = "8f8b8e88-6ef8-490b-b183-b78912ef0011"
    # Create token expired 1 minute ago
    token = create_access_token(
        subject=user_id,
        role="USER",
        expires_delta=timedelta(minutes=-1),
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.code == "AUTH_TOKEN_EXPIRED"


def test_opaque_token_and_hashing() -> None:
    """Verifies 256-bit opaque token generation and SHA-256 hashing."""
    token = generate_opaque_token()
    assert len(token) == 64  # 32 bytes in hex = 64 characters

    token_hash = hash_token(token)
    assert len(token_hash) == 64  # SHA-256 hex is 64 characters

    # Deterministic hashing
    assert hash_token(token) == token_hash

    # Different tokens produce different hashes
    token2 = generate_opaque_token()
    assert hash_token(token2) != token_hash

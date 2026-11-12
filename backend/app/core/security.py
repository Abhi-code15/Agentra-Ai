"""Cryptographic utilities: Argon2id password hashing, JWT minting, and refresh token hashing."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from pwdlib import PasswordHash
from app.core.config import settings
from app.core.exceptions import UnauthorizedException

# Initialize PasswordHash using Argon2id
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Mints a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_hex(16),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and cryptographically verifies a signed JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(
            code="AUTH_TOKEN_EXPIRED",
            message="Access token has expired. Please refresh your session.",
        )
    except jwt.PyJWTError:
        raise UnauthorizedException(
            code="AUTH_TOKEN_INVALID",
            message="Invalid authentication token.",
        )


def generate_opaque_token() -> str:
    """Generates a cryptographically secure random token (256-bit)."""
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    """Generates a SHA-256 hash of an opaque token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

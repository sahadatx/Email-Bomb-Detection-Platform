from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# ---------------------------------------------------------------------------
# Password security
# ---------------------------------------------------------------------------

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class PasswordPolicyError(ValueError):
    """Raised when a password does not satisfy the security policy."""


def validate_password_strength(password: str) -> None:
    """
    Validate the application's password policy.

    Requirements:
    - 12 to 128 characters
    - at least one uppercase character
    - at least one lowercase character
    - at least one digit
    - at least one special character
    """
    if not isinstance(password, str):
        raise PasswordPolicyError("Password must be a string.")

    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordPolicyError(
            f"Password must contain at least {PASSWORD_MIN_LENGTH} characters."
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        raise PasswordPolicyError(
            f"Password must not exceed {PASSWORD_MAX_LENGTH} characters."
        )

    if not any(character.isupper() for character in password):
        raise PasswordPolicyError(
            "Password must contain at least one uppercase character."
        )

    if not any(character.islower() for character in password):
        raise PasswordPolicyError(
            "Password must contain at least one lowercase character."
        )

    if not any(character.isdigit() for character in password):
        raise PasswordPolicyError(
            "Password must contain at least one digit."
        )

    if not any(not character.isalnum() for character in password):
        raise PasswordPolicyError(
            "Password must contain at least one special character."
        )


def hash_password(password: str) -> str:
    """
    Validate and hash a plaintext password using bcrypt.

    Plaintext passwords must never be persisted.
    """
    validate_password_strength(password)
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a stored password hash.
    """
    if not password or not password_hash:
        return False

    try:
        return password_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# JWT / access-token security
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TYPE = "access"

PROTECTED_JWT_CLAIMS = frozenset(
    {
        "sub",
        "jti",
        "type",
        "iat",
        "exp",
    }
)


@dataclass(frozen=True)
class AccessToken:
    """
    Result of access-token creation.
    """

    token: str
    jti: str
    expires_at: datetime


def create_access_token(
    subject: str,
    *,
    expires_minutes: int | None = None,
    claims: dict[str, Any] | None = None,
) -> AccessToken:
    """
    Create a signed JWT access token.

    Standard security claims are generated internally and cannot be
    overridden through the optional claims dictionary.
    """
    if not subject:
        raise ValueError("Token subject must not be empty.")

    lifetime = (
        expires_minutes
        if expires_minutes is not None
        else settings.access_token_expire_minutes
    )

    if lifetime <= 0:
        raise ValueError("Token lifetime must be greater than zero.")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=lifetime)
    jti = str(uuid4())

    payload: dict[str, Any] = {
        "sub": subject,
        "jti": jti,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": expires_at,
    }

    if claims:
        for key, value in claims.items():
            if key in PROTECTED_JWT_CLAIMS:
                continue

            payload[key] = value

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return AccessToken(
        token=token,
        jti=jti,
        expires_at=expires_at,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and cryptographically validate a JWT access token.

    Raises JWTError when the token is invalid or expired.
    """
    if not token:
        raise JWTError("Token is empty.")

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise JWTError("Invalid token type.")

    if not payload.get("sub"):
        raise JWTError("Token subject is missing.")

    if not payload.get("jti"):
        raise JWTError("Token JTI is missing.")

    return payload


def validate_access_token(token: str) -> bool:
    """
    Return True only when the JWT is valid and is an access token.
    """
    try:
        decode_access_token(token)
    except JWTError:
        return False

    return True


def get_token_subject(token: str) -> str:
    """
    Extract the authenticated user ID from a valid access token.
    """
    payload = decode_access_token(token)
    return str(payload["sub"])


def get_token_jti(token: str) -> str:
    """
    Extract the unique session identifier from a valid access token.
    """
    payload = decode_access_token(token)
    return str(payload["jti"])


# ---------------------------------------------------------------------------
# Session security
# ---------------------------------------------------------------------------

def is_session_active(
    *,
    revoked_at: datetime | None,
    expires_at: datetime,
    now: datetime | None = None,
) -> bool:
    """
    Determine whether a server-side session is currently active.

    A session is inactive when:
    - it has been explicitly revoked, or
    - it has expired.
    """
    if revoked_at is not None:
        return False

    current_time = now or datetime.now(timezone.utc)

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at > current_time
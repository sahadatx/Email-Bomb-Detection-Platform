from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.core.security import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    create_access_token,
    decode_access_token,
    get_token_jti,
    get_token_subject,
    hash_password,
    is_session_active,
    validate_access_token,
    validate_password_strength,
    verify_password,
    PasswordPolicyError,
)


# ---------------------------------------------------------------------------
# Password tests
# ---------------------------------------------------------------------------

def test_password_hash_is_not_plaintext() -> None:
    password = "StrongPassword!123"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$2")


def test_password_hash_verifies_correct_password() -> None:
    password = "StrongPassword!123"

    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_password_hash_rejects_wrong_password() -> None:
    password_hash = hash_password("StrongPassword!123")

    assert verify_password("WrongPassword!123", password_hash) is False


def test_password_hashes_are_unique() -> None:
    password = "StrongPassword!123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "lowercaseonly123!",
        "UPPERCASEONLY123!",
        "NoDigitsPassword!",
        "NoSpecialCharacter123",
    ],
)
def test_password_policy_rejects_weak_password(password: str) -> None:
    with pytest.raises(PasswordPolicyError):
        validate_password_strength(password)


def test_password_policy_rejects_password_above_maximum_length() -> None:
    password = (
        "Aa1!"
        + ("x" * PASSWORD_MAX_LENGTH)
    )

    with pytest.raises(PasswordPolicyError):
        validate_password_strength(password)


def test_password_policy_accepts_strong_password() -> None:
    password = "StrongPassword!123"

    validate_password_strength(password)


def test_password_policy_minimum_length_is_defined() -> None:
    assert PASSWORD_MIN_LENGTH == 12


# ---------------------------------------------------------------------------
# JWT tests
# ---------------------------------------------------------------------------

def test_access_token_contains_required_claims() -> None:
    result = create_access_token("user-123")

    payload = decode_access_token(result.token)

    assert payload["sub"] == "user-123"
    assert payload["jti"] == result.jti
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_access_tokens_have_unique_jti() -> None:
    first = create_access_token("user-123")
    second = create_access_token("user-123")

    assert first.jti != second.jti
    assert first.token != second.token


def test_access_token_is_valid() -> None:
    result = create_access_token("user-123")

    assert validate_access_token(result.token) is True


def test_access_token_subject_can_be_extracted() -> None:
    result = create_access_token("user-123")

    assert get_token_subject(result.token) == "user-123"


def test_access_token_jti_can_be_extracted() -> None:
    result = create_access_token("user-123")

    assert get_token_jti(result.token) == result.jti


def test_invalid_access_token_is_rejected() -> None:
    assert validate_access_token("not-a-valid-token") is False


def test_protected_jwt_claims_cannot_be_overridden() -> None:
    result = create_access_token(
        "user-123",
        claims={
            "sub": "attacker",
            "jti": "attacker-jti",
            "type": "refresh",
            "iat": "attacker",
            "exp": "attacker",
            "role": "ADMIN",
        },
    )

    payload = decode_access_token(result.token)

    assert payload["sub"] == "user-123"
    assert payload["jti"] == result.jti
    assert payload["type"] == "access"
    assert payload["iat"] != "attacker"
    assert payload["exp"] != "attacker"

    # Non-protected application claims are allowed.
    assert payload["role"] == "ADMIN"


def test_expired_access_token_is_rejected() -> None:
    result = create_access_token(
        "user-123",
        expires_minutes=1,
    )

    # Build an expired token using the same JTI to verify decoder behavior.
    from jose import jwt
    from app.core.config import settings

    now = datetime.now(timezone.utc)

    expired_payload = {
        "sub": "user-123",
        "jti": result.jti,
        "type": "access",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=5),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(JWTError):
        decode_access_token(expired_token)


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------

def test_active_session_is_active() -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    assert is_session_active(
        revoked_at=None,
        expires_at=expires_at,
    ) is True


def test_revoked_session_is_inactive() -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    revoked_at = datetime.now(timezone.utc)

    assert is_session_active(
        revoked_at=revoked_at,
        expires_at=expires_at,
    ) is False


def test_expired_session_is_inactive() -> None:
    expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    assert is_session_active(
        revoked_at=None,
        expires_at=expires_at,
    ) is False
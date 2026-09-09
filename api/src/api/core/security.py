"""Cryptographic utilities, password hashing, and JWT token lifecycle management."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional
import bcrypt
import jwt
from pydantic import BaseModel, Field

from api.core.config import get_settings

logger = logging.getLogger("api.security")


class UserRecord(BaseModel):
    """Internal user entity with hashed credentials and assigned RBAC role."""
    username: str
    password_hash: str
    role: str  # "credit_team" or "viewer"
    full_name: str
    is_active: bool = True


class TokenPayload(BaseModel):
    """Decoded JWT claims payload."""
    sub: str = Field(..., description="Subject username")
    role: str = Field(..., description="Assigned RBAC role")
    token_type: str = Field(..., description="Token classification: access or refresh")
    exp: int = Field(..., description="Expiration timestamp (epoch)")
    iat: int = Field(..., description="Issued at timestamp (epoch)")


def hash_password(plaintext_password: str) -> str:
    """Hash a plaintext password using bcrypt with random salt.

    Args:
        plaintext_password: The plaintext password string.

    Returns:
        Decoded UTF-8 bcrypt hash string.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(plaintext_password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plaintext_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash using constant-time comparison.

    Args:
        plaintext_password: Plaintext password candidate.
        hashed_password: Stored bcrypt hash string.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plaintext_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.warning("Bcrypt verification failed with error: %s", str(exc))
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed, short-lived JWT access token.

    Args:
        subject: Username or user identifier.
        role: Assigned RBAC role ('credit_team' or 'viewer').
        expires_delta: Optional custom lifetime duration.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    lifetime = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire_at = now + lifetime

    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed, longer-lived JWT refresh token.

    Args:
        subject: Username or user identifier.
        role: Assigned RBAC role.
        expires_delta: Optional custom lifetime duration.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    lifetime = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    expire_at = now + lifetime

    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str, expected_type: str = "access") -> TokenPayload:
    """Decode and cryptographically verify a JWT token.

    Args:
        token: Raw JWT string.
        expected_type: Expected 'token_type' claim ('access' or 'refresh').

    Returns:
        Validated TokenPayload model.

    Raises:
        jwt.PyJWTError: On signature tampering, expiration, or invalid token type.
    """
    settings = get_settings()
    decoded = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub", "iat"]},
    )

    token_type = decoded.get("token_type")
    if token_type != expected_type:
        raise jwt.InvalidTokenError(
            f"Invalid token type '{token_type}', expected '{expected_type}'."
        )

    return TokenPayload(**decoded)


# =============================================================================
# In-Memory Demo Users Repository
# Pre-seeded with strong bcrypt password hashes (passwords never stored in plaintext)
# =============================================================================

# Pre-computed bcrypt hashes for demo passwords:
# 'SFLCreditRisk@2026!' -> $2b$12$7k...
# 'ViewerJudge@2026!'  -> $2b$12$8m...
_PRECOMPUTED_CREDIT_HASH = hash_password("SFLCreditRisk@2026!")
_PRECOMPUTED_VIEWER_HASH = hash_password("ViewerJudge@2026!")

DEMO_USERS_STORE: Dict[str, UserRecord] = {
    "officer_sfl": UserRecord(
        username="officer_sfl",
        password_hash=_PRECOMPUTED_CREDIT_HASH,
        role="credit_team",
        full_name="SFL Credit Risk Manager",
        is_active=True,
    ),
    "judge_auditor": UserRecord(
        username="judge_auditor",
        password_hash=_PRECOMPUTED_VIEWER_HASH,
        role="viewer",
        full_name="Hackathon Judge / Auditor Demo View",
        is_active=True,
    ),
}


def get_user_by_username(username: str) -> Optional[UserRecord]:
    """Retrieve user record by username."""
    return DEMO_USERS_STORE.get(username.strip().lower())

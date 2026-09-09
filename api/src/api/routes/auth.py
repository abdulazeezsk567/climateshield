"""Authentication and session management routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
import jwt
from pydantic import BaseModel, Field

from api.core.config import get_settings
from api.core.dependencies import UserContext, get_current_user_context
from api.core.rate_limiter import rate_limiter
from api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    get_user_by_username,
    verify_password,
)

logger = logging.getLogger("api.auth.routes")

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


class LoginRequest(BaseModel):
    """Credentials payload for JWT bearer token issuance."""
    username: str = Field(..., min_length=3, max_length=50, description="Authorized username identifier")
    password: str = Field(..., min_length=6, max_length=128, description="User secret password")


class RefreshRequest(BaseModel):
    """Payload containing a valid refresh token."""
    refresh_token: str = Field(..., description="Cryptographically signed refresh token")


class TokenResponse(BaseModel):
    """JWT Bearer tokens and session metadata."""
    access_token: str = Field(..., description="Short-lived signed JWT access token")
    refresh_token: str = Field(..., description="Longer-lived signed JWT refresh token")
    token_type: str = Field(default="bearer", description="Token scheme classification")
    expires_in: int = Field(..., description="Access token lifespan in seconds")
    user_id: str = Field(..., description="Authenticated username subject")
    role: str = Field(..., description="Assigned RBAC role")
    full_name: str = Field(..., description="Display name of the user")


class UserProfileResponse(BaseModel):
    """Public profile of the currently authenticated user."""
    username: str
    role: str
    full_name: str
    is_active: bool


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User and Issue JWT Tokens",
    description="Authenticates credentials using salted bcrypt verification, emits brute-force anomaly logs upon repeated failures, and returns signed access and refresh JWT tokens.",
)
async def login(credentials: LoginRequest, request: Request) -> TokenResponse:
    """Validate credentials and issue short-lived access and refresh JWTs."""
    settings = get_settings()

    # Determine caller IP for security anomaly tracking
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")

    user = get_user_by_username(credentials.username)
    if not user or not verify_password(credentials.password, user.password_hash):
        rate_limiter.record_auth_failure(identifier=credentials.username, ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        rate_limiter.record_auth_failure(identifier=credentials.username, ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive or disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.username, role=user.role)
    refresh_token = create_refresh_token(subject=user.username, role=user.role)

    logger.info("Successful login for user='%s' role='%s' from ip=%s", user.username, user.role, client_ip)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user_id=user.username,
        role=user.role,
        full_name=user.full_name,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Expired Access Token",
    description="Exchanges an unexpired refresh token for a newly signed access token without requiring re-entry of credentials.",
)
async def refresh_session(payload: RefreshRequest, request: Request) -> TokenResponse:
    """Validate refresh token and issue fresh access token."""
    settings = get_settings()

    try:
        decoded = decode_jwt_token(payload.refresh_token, expected_type="refresh")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please authenticate again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or tampered refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_username(decoded.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token is no longer active.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue a new access token while retaining the valid refresh token (or rotating)
    new_access_token = create_access_token(subject=user.username, role=user.role)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=payload.refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user_id=user.username,
        role=user.role,
        full_name=user.full_name,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get Current User Profile",
    description="Returns the profile details and RBAC role of the currently authenticated caller.",
)
async def get_current_user_profile(
    current_user: UserContext = Depends(get_current_user_context),
) -> UserProfileResponse:
    """Return caller's identity and assigned role."""
    user = get_user_by_username(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record could not be found.",
        )

    return UserProfileResponse(
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        is_active=user.is_active,
    )

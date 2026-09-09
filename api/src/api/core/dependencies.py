"""FastAPI dependency providers for internal services and stateless auth contexts."""

import logging
from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, status
import jwt
from pydantic import BaseModel, Field

from api.core.config import get_settings
from api.core.security import decode_jwt_token, get_user_by_username
from data_layer import DataLayerService, get_data_layer_service
from integration_layer import IntegrationService, get_integration_service
from risk_engine import RiskEngineService

logger = logging.getLogger("api.auth")


class UserContext(BaseModel):
    """Stateless representation of the calling user identity and verified RBAC role."""
    user_id: str = Field(..., description="Unique subject username")
    role: str = Field(..., description="Assigned RBAC role: credit_team or viewer")
    full_name: Optional[str] = Field(None, description="Display name of user")
    is_authenticated: bool = True


def get_data_layer() -> DataLayerService:
    """Dependency provider for DataLayerService."""
    return get_data_layer_service()


def get_risk_engine() -> RiskEngineService:
    """Dependency provider for RiskEngineService."""
    return RiskEngineService(data_layer=get_data_layer_service())


def get_integration() -> IntegrationService:
    """Dependency provider for IntegrationService."""
    return get_integration_service()


async def get_current_user_context(
    authorization: Optional[str] = Header(None, alias="Authorization", description="Bearer JWT access token"),
) -> UserContext:
    """Extract, decode, and cryptographically verify the caller's JWT Bearer access token.

    Raises:
        HTTPException(401): If authorization header is absent, malformed, expired, or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected format: 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = decode_jwt_token(token, expected_type="access")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please refresh your session.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as err:
        logger.warning("JWT verification failed: %s", str(err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(err)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error("Unexpected error during token decoding: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token could not be verified.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_username(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated or does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserContext(
        user_id=user.username,
        role=user.role,
        full_name=user.full_name,
        is_authenticated=True,
    )


def require_role(*allowed_roles: str) -> Callable:
    """Dependency factory returning an RBAC authorization checker.

    Args:
        *allowed_roles: One or more authorized role names (e.g. 'credit_team', 'viewer').

    Returns:
        FastAPI dependency callable enforcing that the authenticated user possesses one of the allowed roles.
    """
    async def rbac_checker(
        current_user: UserContext = Depends(get_current_user_context),
    ) -> UserContext:
        if current_user.role not in allowed_roles:
            logger.warning(
                "[RBAC_DENIED] Access denied for user='%s' with role='%s'. Required one of: %s",
                current_user.user_id,
                current_user.role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: User role '{current_user.role}' lacks sufficient privileges for this action.",
            )
        return current_user

    return rbac_checker

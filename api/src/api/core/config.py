"""API Service configuration and settings model."""

from functools import lru_cache
import logging
from typing import List
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Central configuration for ClimateShield API service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", description="Runtime environment: development, staging, production")
    port: int = Field(default=8000, description="Listening TCP port")
    host: str = Field(default="0.0.0.0", description="Listening IP address")
    log_level: str = Field(default="info", description="Logging verbosity")
    log_format: str = Field(default="text", description="Log format: json or text")

    # Security & Tokens (Loaded strictly from environment)
    jwt_secret_key: str = Field(
        default="development-insecure-secret-change-in-production",
        description="HMAC signing key for JWT tokens",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT encryption algorithm")
    access_token_expire_minutes: int = Field(default=15, description="Short-lived access token TTL in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token TTL in days")

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Enforce strict secret provisioning without fallback defaults in staging/production."""
        if self.environment in ("staging", "production"):
            if not self.jwt_secret_key or "development-insecure" in self.jwt_secret_key:
                raise ValueError(
                    f"CRITICAL SECURITY CONFIGURATION ERROR: jwt_secret_key cannot use default development "
                    f"placeholder in '{self.environment}' environment. A cryptographically secure secret must be provided."
                )
        return self

    # Rate Limiting Settings
    rate_limit_auth_per_minute: int = Field(default=5, description="Rate limit on auth login/refresh attempts per IP per minute")
    rate_limit_general_per_minute: int = Field(default=60, description="General endpoint rate limit per IP per minute")
    rate_limit_authenticated_per_minute: int = Field(default=120, description="Rate limit per authenticated token per minute")

    # Transport Security
    enforce_hsts: bool = Field(default=False, description="Whether to send Strict-Transport-Security header")

    # CORS configuration - strict, non-wildcard
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-delimited permitted CORS origins (wildcards forbidden)",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parsed list of allowed CORS origins, strictly forbidding '*'."""
        raw_list = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        sanitized = []
        for origin in raw_list:
            if origin == "*":
                logger.warning("Wildcard CORS origin '*' was configured and has been rejected for security reasons.")
                continue
            sanitized.append(origin)
        return sanitized or ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton provider for application settings."""
    return Settings()

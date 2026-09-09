"""Security headers, HSTS, and rate limiting HTTP middleware."""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.core.config import get_settings
from api.core.errors import ErrorDetail, ErrorResponse
from api.core.rate_limiter import rate_limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP security headers into all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        settings = get_settings()

        # Modern Content Security Policy disallowing inline eval, frames, and object embeds
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self';"
        )
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking / framing
        response.headers["X-Frame-Options"] = "DENY"
        # Cross-Site Scripting filter
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HTTP Strict Transport Security (HSTS)
        if settings.enforce_hsts or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Prevent browser caching of sensitive borrower and credit risk data
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Enforces per-IP sliding-window rate limits on all incoming API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bypass rate limiter for OpenAPI docs and health checks
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        settings = get_settings()

        # Extract client IP address (supporting X-Forwarded-For if behind a reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        # Apply stricter rate limit on authentication endpoints to blunt brute-force attempts
        if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/refresh"):
            limit = settings.rate_limit_auth_per_minute
            key = f"auth_ip:{client_ip}"
        else:
            limit = settings.rate_limit_general_per_minute
            key = f"general_ip:{client_ip}"

        is_limited, retry_after = rate_limiter.is_rate_limited(key=key, limit=limit, window_seconds=60)

        if is_limited:
            error_resp = ErrorResponse(
                error=ErrorDetail(
                    code="RATE_LIMIT_EXCEEDED",
                    message=f"Too many requests. Rate limit exceeded for this origin. Retry after {retry_after} seconds.",
                    details={"retry_after_seconds": retry_after, "limit_per_minute": limit},
                )
            )
            resp = JSONResponse(
                status_code=429,
                content=error_resp.model_dump(mode="json"),
            )
            resp.headers["Retry-After"] = str(retry_after)
            return resp

        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Measures latency, throughput, and error rates, recording into the MetricsRegistry."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import time
        from climateshield_shared.telemetry import get_metrics_registry

        start_time = time.perf_counter()
        registry = get_metrics_registry()
        path = request.url.path

        try:
            response: Response = await call_next(request)
            duration = time.perf_counter() - start_time
            registry.increment_http_requests(request.method, path, response.status_code)
            registry.observe_http_duration(path, duration)

            if response.status_code >= 400:
                registry.increment_http_errors(response.status_code, f"STATUS_{response.status_code}")

            return response
        except Exception as exc:
            duration = time.perf_counter() - start_time
            registry.increment_http_requests(request.method, path, 500)
            registry.observe_http_duration(path, duration)
            registry.increment_http_errors(500, type(exc).__name__)
            raise


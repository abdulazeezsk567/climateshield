"""Comprehensive security, authentication, and RBAC test suite for ClimateShield API."""

import pytest
from fastapi.testclient import TestClient
from api.core.rate_limiter import rate_limiter
from api.core.security import create_access_token, create_refresh_token
from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    """Reset rate limiter state before each test so tests don't interfere."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def get_auth_header(username: str = "officer_sfl", role: str = "credit_team") -> dict:
    """Helper creating a valid Authorization Bearer header."""
    token = create_access_token(subject=username, role=role)
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. AUTHENTICATION (LOGIN, REFRESH, ME)
# =============================================================================

def test_login_success_credit_officer():
    """Verify login with valid officer credentials returns access and refresh tokens."""
    payload = {
        "username": "officer_sfl",
        "password": "SFLCreditRisk@2026!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == "officer_sfl"
    assert data["role"] == "credit_team"
    assert data["expires_in"] == 15 * 60  # 15 minutes


def test_login_success_judge_viewer():
    """Verify login with valid judge credentials returns viewer role tokens."""
    payload = {
        "username": "judge_auditor",
        "password": "ViewerJudge@2026!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "judge_auditor"
    assert data["role"] == "viewer"


def test_login_invalid_password():
    """Verify login fails with structured 401 when password is incorrect."""
    payload = {
        "username": "officer_sfl",
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid username or password" in data["error"]["message"]


def test_login_nonexistent_user():
    """Verify login fails with 401 when username does not exist."""
    payload = {
        "username": "non_existent_hacker",
        "password": "SomePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_refresh_token_flow():
    """Verify exchanging a valid refresh token yields a new valid access token."""
    refresh_token = create_refresh_token(subject="officer_sfl", role="credit_team")
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["user_id"] == "officer_sfl"
    assert data["role"] == "credit_team"


def test_refresh_token_invalid():
    """Verify submitting a tampered refresh token returns 401."""
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "tampered.jwt.signature"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_get_current_user_profile():
    """Verify /api/v1/auth/me returns current user identity with valid token."""
    headers = get_auth_header("officer_sfl", "credit_team")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["username"] == "officer_sfl"
    assert data["role"] == "credit_team"
    assert data["is_active"] is True


def test_get_current_user_profile_unauthenticated():
    """Verify /api/v1/auth/me rejects unauthenticated requests with 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


# =============================================================================
# 2. ROLE-BASED ACCESS CONTROL (RBAC) ENFORCEMENT
# =============================================================================

def test_rbac_viewer_can_read_portfolio():
    """Verify viewer role is permitted to read portfolio summary."""
    headers = get_auth_header("judge_auditor", "viewer")
    response = client.get("/api/v1/portfolio/summary", headers=headers)
    assert response.status_code == 200


def test_rbac_viewer_forbidden_from_trigger_simulation():
    """Verify viewer role is strictly forbidden (HTTP 403) from initiating trigger simulations."""
    headers = get_auth_header("judge_auditor", "viewer")
    payload = {
        "district": "GORAKHPUR",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 1.5,
    }
    response = client.post("/api/v1/triggers/simulate", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    assert "lacks sufficient privileges" in data["error"]["message"]


def test_rbac_credit_team_permitted_trigger_simulation():
    """Verify credit_team role is authorized to execute trigger simulation."""
    headers = get_auth_header("officer_sfl", "credit_team")
    payload = {
        "district": "GORAKHPUR",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 1.5,
    }
    response = client.post("/api/v1/triggers/simulate", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["triggers_activated"] > 0


# =============================================================================
# 3. DEFENSIVE SECURITY HEADERS
# =============================================================================

def test_defensive_http_security_headers_present():
    """Verify modern security headers are injected into all HTTP responses."""
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert "Content-Security-Policy" in headers
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_sensitive_endpoints_prevent_caching():
    """Verify sensitive financial /api/v1 endpoints mandate Cache-Control: no-store."""
    headers = get_auth_header("officer_sfl", "credit_team")
    response = client.get("/api/v1/portfolio/summary", headers=headers)
    assert response.status_code == 200

    assert "no-store" in response.headers.get("Cache-Control", "")
    assert response.headers.get("Pragma") == "no-cache"


# =============================================================================
# 4. SLIDING-WINDOW RATE LIMITING & BRUTE FORCE DEFENSE
# =============================================================================

def test_rate_limiting_auth_endpoints():
    """Verify authentication endpoint rate limiting triggers 429 after threshold."""
    payload = {
        "username": "officer_sfl",
        "password": "WrongPassword!",
    }

    # Auth rate limit is 5 req/min. The 6th request from same IP should receive 429
    responses = []
    for _ in range(6):
        resp = client.post("/api/v1/auth/login", json=payload)
        responses.append(resp)

    # First 5 should be 401 (invalid credentials)
    for r in responses[:5]:
        assert r.status_code == 401

    # 6th request should be 429 Too Many Requests
    assert responses[5].status_code == 429
    assert "Retry-After" in responses[5].headers
    data = responses[5].json()
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"


# =============================================================================
# 5. INPUT VALIDATION & INJECTION RESISTANCE
# =============================================================================

def test_path_parameter_regex_validation():
    """Verify path parameter regex rejects directory traversal attempts."""
    headers = get_auth_header("officer_sfl", "credit_team")

    # Attempt path traversal in borrower_id
    response = client.get("/api/v1/risk/borrowers/..%2F..%2Fetc%2Fpasswd", headers=headers)
    # Either 404 or 422, but strictly not 200 or 500
    assert response.status_code in (404, 422)


def test_simulation_district_regex_validation():
    """Verify trigger simulation rejects malicious injection strings in district name."""
    headers = get_auth_header("officer_sfl", "credit_team")
    payload = {
        "district": "<script>alert('pwned')</script>",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 1.5,
    }
    response = client.post("/api/v1/triggers/simulate", json=payload, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

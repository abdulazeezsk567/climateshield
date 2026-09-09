"""Extended API integration, security, and rate-limit test suite for ClimateShield."""

import pytest
from fastapi.testclient import TestClient
from api.core.rate_limiter import rate_limiter
from api.core.security import create_access_token
from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def get_token_header(username: str = "officer_sfl", role: str = "credit_team") -> dict:
    token = create_access_token(subject=username, role=role)
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. AUTH-REQUIRED-BUT-MISSING TESTS
# =============================================================================

@pytest.mark.parametrize(
    "method,endpoint",
    [
        ("GET", "/api/v1/portfolio/summary"),
        ("GET", "/api/v1/portfolio/heatmap"),
        ("GET", "/api/v1/risk/borrowers"),
        ("GET", "/api/v1/triggers/active"),
        ("GET", "/api/v1/interventions"),
        ("GET", "/api/v1/audit/interventions"),
        ("GET", "/api/v1/audit/verify"),
        ("POST", "/api/v1/triggers/simulate"),
    ],
)
def test_endpoints_reject_missing_auth_header(method, endpoint):
    """Verify all sensitive endpoints reject unauthenticated requests with 401."""
    if method == "GET":
        resp = client.get(endpoint)
    else:
        resp = client.post(endpoint, json={"district": "Varanasi", "hazard_type": "FLOOD_SURGE"})

    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] in ["UNAUTHORIZED", "AUTHENTICATION_REQUIRED"]


# =============================================================================
# 2. WRONG-ROLE (RBAC) TESTS
# =============================================================================

def test_viewer_role_forbidden_from_trigger_simulation():
    """Verify viewer/auditor role cannot execute trigger simulations or mutate LMS state."""
    viewer_headers = get_token_header("judge_auditor", "viewer")
    payload = {
        "district": "Varanasi",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 1.5,
    }
    resp = client.post("/api/v1/triggers/simulate", json=payload, headers=viewer_headers)
    assert resp.status_code == 403
    data = resp.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_credit_team_permitted_to_trigger_simulation():
    """Verify credit_team role is authorized to execute trigger simulations."""
    credit_headers = get_token_header("officer_sfl", "credit_team")
    payload = {
        "district": "Varanasi",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 1.5,
    }
    resp = client.post("/api/v1/triggers/simulate", json=payload, headers=credit_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["district"].upper() == "VARANASI"
    assert "triggers_activated" in data


# =============================================================================
# 3. MALFORMED-INPUT & BOUNDARY VALIDATION
# =============================================================================

def test_negative_pagination_page_rejected():
    """Verify negative page query parameter is rejected with structured 422."""
    headers = get_token_header()
    resp = client.get("/api/v1/risk/borrowers?page=-1&page_size=20", headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_out_of_range_page_size_rejected():
    """Verify page_size exceeding 100 is rejected with structured 422."""
    headers = get_token_header()
    resp = client.get("/api/v1/risk/borrowers?page=1&page_size=500", headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_min_risk_score_rejected():
    """Verify min_risk_score > 100 is rejected with 422."""
    headers = get_token_header()
    resp = client.get("/api/v1/risk/borrowers?min_risk_score=999", headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_empty_json_body_in_simulation_rejected():
    """Verify empty body to simulation endpoint returns 422 validation error."""
    headers = get_token_header("officer_sfl", "credit_team")
    resp = client.post("/api/v1/triggers/simulate", json={}, headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


# =============================================================================
# 4. LOAD & BURST RATE-LIMITING TESTS
# =============================================================================

def test_auth_burst_rate_limiting_triggers_429():
    """Verify rapid burst of auth requests enforces 5 req/min threshold and returns 429."""
    login_payload = {
        "username": "officer_sfl",
        "password": "WrongPassword!",
    }

    # Dispatch 10 consecutive rapid requests from the same test client IP
    responses = [client.post("/api/v1/auth/login", json=login_payload) for _ in range(8)]

    # First 5 should be 401
    for r in responses[:5]:
        assert r.status_code == 401

    # 6th and onward must be 429 Too Many Requests
    for r in responses[5:]:
        assert r.status_code == 429
        assert "Retry-After" in r.headers
        assert r.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


# =============================================================================
# 5. INJECTION RESISTANCE & SECURITY DEFENSES
# =============================================================================

def test_sql_injection_strings_handled_safely():
    """Verify SQL injection strings in district query parameter do not crash the service."""
    headers = get_token_header()
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE borrowers;--",
        "UNION SELECT null, username, password FROM users--",
    ]

    for sqli in sqli_payloads:
        resp = client.get(f"/api/v1/risk/borrowers?district={sqli}", headers=headers)
        # Should return 200 with empty list or 422/404, never 500
        assert resp.status_code in [200, 404, 422]
        if resp.status_code == 200:
            assert resp.json()["items"] == []


def test_xss_script_tags_rejected_in_simulation():
    """Verify XSS script tags in district names are rejected with 422."""
    headers = get_token_header("officer_sfl", "credit_team")
    xss_payloads = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert(1)",
    ]

    for xss in xss_payloads:
        resp = client.post(
            "/api/v1/triggers/simulate",
            json={"district": xss, "hazard_type": "FLOOD_SURGE"},
            headers=headers,
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_defensive_http_headers_present_on_all_responses():
    """Verify essential defensive security headers exist on API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "content-security-policy" in headers

    # Test sensitive endpoint over HTTPS
    headers_auth = get_token_header("officer_sfl", "credit_team")
    https_resp = client.get("https://testserver/api/v1/portfolio/summary", headers=headers_auth)
    assert https_resp.status_code == 200
    assert "strict-transport-security" in https_resp.headers
    assert "no-store" in https_resp.headers.get("cache-control", "")

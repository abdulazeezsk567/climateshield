"""Comprehensive API layer integration and endpoint test suite."""

import pytest
from fastapi.testclient import TestClient

from api.core.rate_limiter import rate_limiter
from api.core.security import create_access_token
from api.main import app

_AUTH_TOKEN = create_access_token(subject="officer_sfl", role="credit_team")
client = TestClient(app, headers={"Authorization": f"Bearer {_AUTH_TOKEN}"})


@pytest.fixture(autouse=True)
def reset_rate_limiter_fixture():
    """Reset rate limiter state before each test so tests don't interfere."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


# =============================================================================
# 1. HEALTH AND READINESS PROBE
# =============================================================================

def test_health_check_endpoint():
    """Verify service health endpoint returns 200 and subsystem statuses."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "climateshield-api"
    assert data["version"] == "0.1.0"
    assert "subsystems" in data
    assert data["subsystems"]["risk_engine"] == "UP"


# =============================================================================
# 2. PORTFOLIO ENDPOINTS
# =============================================================================

def test_portfolio_summary_endpoint():
    """Verify /api/v1/portfolio/summary returns non-empty portfolio exposure metrics."""
    response = client.get("/api/v1/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_active_borrowers"] > 0
    assert data["total_credit_exposure"] > 0.0
    assert data["districts_monitored"] >= 7
    assert "GORAKHPUR" in data["active_districts"]
    assert 0.0 <= data["high_risk_exposure_percentage"] <= 100.0


def test_portfolio_heatmap_endpoint():
    """Verify /api/v1/portfolio/heatmap returns geospatial nodes with centroids."""
    response = client.get("/api/v1/portfolio/heatmap")
    assert response.status_code == 200
    nodes = response.json()
    assert isinstance(nodes, list)
    assert len(nodes) >= 7

    gorakhpur_node = next((n for n in nodes if n["district"] == "GORAKHPUR"), None)
    assert gorakhpur_node is not None
    assert gorakhpur_node["latitude"] > 0
    assert gorakhpur_node["longitude"] > 0
    assert gorakhpur_node["borrower_count"] > 0
    assert gorakhpur_node["total_exposure"] > 0
    assert 0.0 <= gorakhpur_node["average_risk_score"] <= 100.0
    assert "risk_tier" in gorakhpur_node
    assert "primary_hazard" in gorakhpur_node


# =============================================================================
# 3. BORROWER RISK ENDPOINTS & PAGINATION
# =============================================================================

def test_list_borrowers_paginated_default():
    """Verify paginated borrower risk list with default parameters."""
    response = client.get("/api/v1/risk/borrowers?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total_items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10
    assert data["total_items"] >= 56
    assert data["has_next"] is True
    assert data["has_prev"] is False

    # Check item schema
    item = data["items"][0]
    assert "borrower_id" in item
    assert "sector" in item
    assert "risk_score" in item
    assert 0.0 <= item["risk_score"] <= 100.0


def test_list_borrowers_sector_filter():
    """Verify borrower risk query with sector filter."""
    response = client.get("/api/v1/risk/borrowers?sector=AGRI_ALLIED&page=1&page_size=50")
    assert response.status_code == 200
    data = response.json()
    assert all(b["sector"] == "AGRI_ALLIED" for b in data["items"])


def test_get_borrower_risk_detail_success():
    """Verify detailed risk scorecard for a valid borrower."""
    # First get a valid borrower ID
    list_res = client.get("/api/v1/risk/borrowers?page_size=1")
    b_id = list_res.json()["items"][0]["borrower_id"]

    response = client.get(f"/api/v1/risk/borrowers/{b_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["borrower"]["borrower_id"] == b_id
    assert "risk_assessment" in data
    assert "district_monthly_baseline" in data
    assert "latest_telemetry" in data
    assert "model_feature_contributions" in data
    assert "rainfall_deficit_ratio" in data["model_feature_contributions"]


def test_get_borrower_risk_detail_not_found():
    """Verify structured 404 error envelope when borrower is not found."""
    response = client.get("/api/v1/risk/borrowers/NON_EXISTENT_ID_9999")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "NON_EXISTENT_ID_9999" in data["error"]["message"]
    assert "traceback" not in data
    assert "exception" not in data


# =============================================================================
# 4. TRIGGER SIMULATION & AUDIT DISPATCH
# =============================================================================

def test_simulate_drought_scenario():
    """Verify on-demand trigger simulation for drought shock scenario."""
    payload = {
        "district": "GORAKHPUR",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 1.8,
    }
    response = client.post("/api/v1/triggers/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["district"] == "GORAKHPUR"
    assert data["hazard_type"] == "DROUGHT_DEFICIT"
    assert data["total_borrowers_evaluated"] > 0
    assert data["triggers_activated"] > 0
    assert data["generated_lms_actions_count"] > 0
    assert data["total_relief_exposure"] > 0
    assert data["sample_trigger_event"] is not None
    assert data["sample_trigger_event"]["recommended_action"]["action_type"] == "EMI_DEFERRAL"


def test_list_active_triggers():
    """Verify /api/v1/triggers/active returns simulation triggers."""
    response = client.get("/api/v1/triggers/active")
    assert response.status_code == 200
    triggers = response.json()
    assert isinstance(triggers, list)
    assert len(triggers) > 0


# =============================================================================
# 5. AUDIT TRAIL & CRYPTOGRAPHIC VERIFICATION
# =============================================================================

def test_audit_interventions_paginated():
    """Verify paginated audit trail of LMS executions and alerts."""
    response = client.get("/api/v1/audit/interventions?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert len(data["items"]) > 0
    entry = data["items"][0]
    assert "audit_id" in entry
    assert "event_type" in entry
    assert "event_hash" in entry
    assert "previous_hash" in entry
    assert "payload_snapshot" in entry


def test_audit_ledger_cryptographic_verification():
    """Verify cryptographic SHA-256 chain integrity endpoint."""
    response = client.get("/api/v1/audit/verify")
    assert response.status_code == 200
    data = response.json()

    assert data["chain_valid"] is True
    assert data["total_entries"] > 0
    assert data["latest_hash"] is not None
    assert len(data["latest_hash"]) == 64  # SHA-256 hex string length


# =============================================================================
# 6. STRUCTURED ERROR HANDLING AND VALIDATION
# =============================================================================

def test_validation_error_structured_response():
    """Verify 422 validation error produces structured envelope without internal trace leaks."""
    # Invalid intensity multiplier (> 5.0)
    payload = {
        "district": "GORAKHPUR",
        "hazard_type": "DROUGHT_DEFICIT",
        "intensity_multiplier": 25.0,  # Exceeds max 5.0
    }
    response = client.post("/api/v1/triggers/simulate", json=payload)
    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert isinstance(data["error"]["details"], list)
    # Ensure no internal python stack traces or paths leaked
    assert "traceback" not in str(data).lower()
    assert "c:\\" not in str(data).lower()

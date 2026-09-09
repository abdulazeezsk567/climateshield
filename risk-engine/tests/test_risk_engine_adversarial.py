"""Dedicated adversarial, edge-case, and boundary unit tests for Risk Engine."""

import asyncio
from datetime import datetime, timezone
from pydantic import ValidationError
import pytest
from climateshield_shared.constants import (
    ClimateHazardType,
    TriggerActionType,
)
from climateshield_shared.schemas.borrower import Borrower, BorrowerSector, GeoLocation, LoanSummary
from climateshield_shared.schemas.climate import ClimateObservation, DataSourceType
from data_layer.baselines.interfaces import HistoricalClimateBaseline
from risk_engine.service import RiskEngineService


@pytest.fixture
def sample_borrower() -> Borrower:
    return Borrower(
        borrower_id="SFL-TEST-ADV-01",
        anonymized_alias="Ganga Feed Mills",
        sector=BorrowerSector.AGRI_ALLIED,
        location=GeoLocation(
            latitude=25.31,
            longitude=82.97,
            district="VARANASI",
            state="Uttar Pradesh",
            pin_code="221001",
        ),
        active_loans=[
            LoanSummary(
                loan_id="LN-ADV-01",
                disbursed_principal=500000.0,
                current_outstanding_balance=400000.0,
                monthly_emi_amount=15000.0,
                tenure_months_remaining=24,
                currency="INR",
            )
        ],
        total_active_exposure=400000.0,
        contact_token="TOKEN_ADV",
    )


@pytest.fixture
def sample_baseline() -> HistoricalClimateBaseline:
    return HistoricalClimateBaseline(
        district_id="VARANASI",
        month_of_year=8,
        avg_rainfall_mm=250.0,
        rainfall_std_dev_mm=60.0,
        rainfall_95th_percentile_mm=380.0,
        avg_max_temp_celsius=32.0,
        avg_ndvi_vegetation_index=0.70,
    )


def test_adversarial_negative_precipitation_rejected_by_schema(sample_borrower):
    """Verify that physically impossible negative precipitation is strictly rejected by schema validation."""
    with pytest.raises(ValidationError) as exc_info:
        ClimateObservation(
            timestamp=datetime.now(timezone.utc),
            location=sample_borrower.location,
            source=DataSourceType.NASA_POWER,
            precipitation_mm=-150.0,  # Negative precipitation
            temperature_celsius=32.0,
            relative_humidity_pct=40.0,
            wind_speed_kmh=10.0,
            ndvi_vegetation_index=0.45,
        )
    assert "precipitation_mm" in str(exc_info.value)


def test_adversarial_extreme_hyperthermia(sample_borrower, sample_baseline):
    """Verify extreme heatwave temperature (>65°C) yields elevated risk score without numerical overflow."""
    service = RiskEngineService()
    obs = ClimateObservation(
        timestamp=datetime.now(timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=0.0,
        temperature_celsius=68.5,  # Extreme heat shock
        relative_humidity_pct=15.0,
        wind_speed_kmh=25.0,
        ndvi_vegetation_index=0.30,
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, obs, sample_baseline))
    assert result.risk_score > 50.0
    assert result.trigger_fired is True
    assert result.recommended_action is not None


def test_boundary_threshold_exact_p95_precision(sample_borrower, sample_baseline):
    """Verify precision around exact 95th percentile trigger boundary (380.0 mm)."""
    service = RiskEngineService()

    # Case A: Exactly below threshold (350.0 mm vs 380mm P95) -> Excess rainfall should not trigger
    obs_below = ClimateObservation(
        timestamp=datetime.now(timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=350.0,
        temperature_celsius=30.0,
        relative_humidity_pct=75.0,
        wind_speed_kmh=12.0,
        ndvi_vegetation_index=0.70,
    )
    res_below = asyncio.run(service.assess_borrower_risk(sample_borrower, obs_below, sample_baseline))
    assert not res_below.trigger_fired

    # Case B: Above threshold (410.0 mm vs 380mm P95) -> Excess rainfall SHOULD trigger
    obs_above = ClimateObservation(
        timestamp=datetime.now(timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=410.0,
        temperature_celsius=30.0,
        relative_humidity_pct=85.0,
        wind_speed_kmh=20.0,
        ndvi_vegetation_index=0.70,
    )
    res_above = asyncio.run(service.assess_borrower_risk(sample_borrower, obs_above, sample_baseline))

    assert res_above.trigger_fired is True
    assert res_above.recommended_action is not None
    assert res_above.recommended_action.action_type in [
        TriggerActionType.RECOVERY_TOPUP,
        TriggerActionType.EMI_DEFERRAL,
        TriggerActionType.TENURE_EXTENSION,
    ]


def test_zero_exposure_empty_loans_resilience(sample_baseline):
    """Verify borrower with 0 loans and 0 exposure evaluates cleanly without zero-division error."""
    service = RiskEngineService()
    zero_borrower = Borrower(
        borrower_id="SFL-ZERO-01",
        anonymized_alias="New Registration Borrower",
        sector=BorrowerSector.SERVICES_LIGHT_MANUFACTURING,
        location=GeoLocation(
            latitude=25.31,
            longitude=82.97,
            district="VARANASI",
            state="Uttar Pradesh",
            pin_code="221001",
        ),
        active_loans=[],
        total_active_exposure=0.0,
        contact_token="TOKEN_ZERO",
    )

    obs = ClimateObservation(
        timestamp=datetime.now(timezone.utc),
        location=zero_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=250.0,
        temperature_celsius=32.0,
        relative_humidity_pct=65.0,
        wind_speed_kmh=10.0,
        ndvi_vegetation_index=0.68,
    )

    result = asyncio.run(service.assess_borrower_risk(zero_borrower, obs, sample_baseline))
    assert 0.0 <= result.risk_score <= 100.0
    assert result.trigger_fired is False

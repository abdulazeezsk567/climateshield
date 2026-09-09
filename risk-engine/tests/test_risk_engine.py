"""Comprehensive unit tests for ClimateShield Risk Engine."""

from datetime import datetime, timezone
import pytest
from climateshield_shared.constants import (
    ClimateHazardType,
    RiskTier,
    TriggerActionType,
)
from climateshield_shared.schemas.borrower import Borrower, BorrowerSector, GeoLocation, LoanSummary
from climateshield_shared.schemas.climate import ClimateObservation, DataSourceType
from data_layer.baselines.interfaces import HistoricalClimateBaseline
from risk_engine.config.loader import RiskEngineConfig
from risk_engine.ml_zoning.model import ExplainableMLZoningModel
from risk_engine.service import RiskEngineService
from risk_engine.thresholds.evaluator import RuleBasedTriggerEvaluator


@pytest.fixture
def sample_borrower() -> Borrower:
    """Fixture for a sample agricultural MSME borrower."""
    return Borrower(
        borrower_id="SFL-TEST-AGRI-01",
        anonymized_alias="Kisan Fertilizer Hub",
        sector=BorrowerSector.AGRI_ALLIED,
        location=GeoLocation(
            latitude=26.76,
            longitude=83.37,
            district="GORAKHPUR",
            state="Uttar Pradesh",
            pin_code="273001",
        ),
        active_loans=[
            LoanSummary(
                loan_id="LN-TEST-01",
                disbursed_principal=200000.0,
                current_outstanding_balance=150000.0,
                monthly_emi_amount=7500.0,
                tenure_months_remaining=18,
                currency="INR",
            )
        ],
        total_active_exposure=150000.0,
        contact_token="TOKEN_TEST",
    )


@pytest.fixture
def sample_baseline() -> HistoricalClimateBaseline:
    """Fixture for Gorakhpur July monsoon baseline."""
    return HistoricalClimateBaseline(
        district_id="GORAKHPUR",
        month_of_year=7,
        avg_rainfall_mm=290.0,
        rainfall_std_dev_mm=87.0,
        rainfall_95th_percentile_mm=478.5,
        avg_max_temp_celsius=33.5,
        avg_ndvi_vegetation_index=0.74,
    )


import asyncio

# =============================================================================
# 1. NORMAL CASE TESTS
# =============================================================================

def test_normal_operating_conditions(sample_borrower, sample_baseline):
    """Normal Case: Rainfall and temperature within expected tolerance -> No trigger."""
    service = RiskEngineService()

    # Normal observation (280mm vs 290mm baseline, only -3.4% deficit)
    normal_obs = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=280.0,
        temperature_celsius=33.0,
        relative_humidity_pct=78.0,
        wind_speed_kmh=14.0,
        ndvi_vegetation_index=0.72,
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, normal_obs, sample_baseline))

    assert result.borrower_id == sample_borrower.borrower_id
    assert not result.trigger_fired
    assert result.recommended_action is None
    assert result.risk_score < 40.0
    assert isinstance(result.evaluated_at, datetime)


def test_normal_drought_trigger_activation(sample_borrower, sample_baseline):
    """Normal Case: Severe deficit (-50%) crosses AGRI_ALLIED -35% threshold -> Fires EMI deferral."""
    service = RiskEngineService()

    # Severe deficit: 145mm vs 290mm baseline (-50.0% deficit)
    drought_obs = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=145.0,
        temperature_celsius=36.5,
        relative_humidity_pct=52.0,
        wind_speed_kmh=18.0,
        ndvi_vegetation_index=0.55,
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, drought_obs, sample_baseline))

    assert result.trigger_fired is True
    assert result.recommended_action is not None
    assert result.recommended_action.action_type == TriggerActionType.EMI_DEFERRAL
    assert result.recommended_action.relief_period_days == 30
    assert "Rainfall deficit" in result.trigger_reason
    assert result.risk_score >= 40.0


def test_normal_excess_rainfall_trigger(sample_borrower, sample_baseline):
    """Normal Case: Extreme rainfall (520mm vs 478.5mm p95) -> Fires recovery topup."""
    service = RiskEngineService()

    flood_obs = ClimateObservation(
        timestamp=datetime(2026, 7, 20, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=520.0,
        temperature_celsius=28.0,
        relative_humidity_pct=95.0,
        wind_speed_kmh=35.0,
        ndvi_vegetation_index=0.70,
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, flood_obs, sample_baseline))

    assert result.trigger_fired is True
    assert result.recommended_action is not None
    assert result.recommended_action.action_type == TriggerActionType.RECOVERY_TOPUP
    # 10% of 150,000 exposure = 15,000 topup
    assert result.recommended_action.topup_amount == 15000.0


# =============================================================================
# 2. MISSING DATA CASE TESTS
# =============================================================================

def test_missing_ndvi_and_humidity_telemetry(sample_borrower, sample_baseline):
    """Missing Data Case: Missing satellite NDVI and humidity should not crash the engine,
    and should populate appropriate basis risk quality flags.
    """
    service = RiskEngineService()

    obs_with_nulls = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=100.0,  # deficit
        temperature_celsius=34.0,
        relative_humidity_pct=None,  # Missing
        wind_speed_kmh=None,         # Missing
        ndvi_vegetation_index=None,  # Missing (e.g. monsoon cloud cover)
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, obs_with_nulls, sample_baseline))

    assert result.trigger_fired is True
    assert "MISSING_SATELLITE_NDVI_CONFIRMATION" in result.basis_risk_flags
    assert "UNCONFIRMED_HUMIDITY_TELEMETRY" in result.basis_risk_flags
    assert 0.0 <= result.risk_score <= 100.0


# =============================================================================
# 3. BOUNDARY THRESHOLD CASE TESTS
# =============================================================================

def test_boundary_threshold_precision(sample_borrower, sample_baseline):
    """Boundary Case: Evaluator tested precisely at -35% threshold boundary.
    Baseline = 290.0mm.
    -35.0% threshold corresponds to exactly 188.5mm.
    """
    evaluator = RuleBasedTriggerEvaluator()

    # Just above threshold: 188.55mm (-34.98% deficit) -> Should NOT fire
    obs_just_above = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=188.55,
        temperature_celsius=33.5,
        ndvi_vegetation_index=0.74,
    )
    fired_above, _, _, _ = evaluator.evaluate(sample_borrower, obs_just_above, sample_baseline)
    assert fired_above is False

    # Just below threshold: 188.45mm (-35.01% deficit) -> MUST fire
    obs_just_below = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=188.45,
        temperature_celsius=33.5,
        ndvi_vegetation_index=0.74,
    )
    fired_below, reason_below, action_below, hazard_below = evaluator.evaluate(
        sample_borrower, obs_just_below, sample_baseline
    )
    assert fired_below is True
    assert hazard_below == ClimateHazardType.DROUGHT_DEFICIT
    assert action_below.action_type == TriggerActionType.EMI_DEFERRAL


def test_boundary_proximity_flag_detection(sample_borrower, sample_baseline):
    """Boundary Case: When rainfall is within 3% of trigger boundary, flag should be raised."""
    service = RiskEngineService()

    # 185.0mm is -36.2% deficit (very close to -35.0% cutoff)
    obs_near = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=185.0,
        temperature_celsius=33.5,
        ndvi_vegetation_index=0.74,
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, obs_near, sample_baseline))
    assert "BOUNDARY_THRESHOLD_PROXIMITY" in result.basis_risk_flags


# =============================================================================
# 4. ADVERSARIAL / EXTREME INPUT CASE TESTS
# =============================================================================

def test_adversarial_extreme_and_negative_inputs(sample_borrower, sample_baseline):
    """Adversarial Case: Negative/corrupt inputs are caught by schema validation,
    and extreme outlier inputs are clamped and sanitized without crashing.
    """
    from pydantic import ValidationError

    # 1. Negative / out-of-bounds numbers rejected by Pydantic schema
    with pytest.raises(ValidationError):
        ClimateObservation(
            timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
            location=sample_borrower.location,
            source=DataSourceType.NASA_POWER,
            precipitation_mm=-250.0,  # Negative rain rejected
            temperature_celsius=35.0,
        )

    with pytest.raises(ValidationError):
        ClimateObservation(
            timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
            location=sample_borrower.location,
            source=DataSourceType.NASA_POWER,
            precipitation_mm=50.0,
            temperature_celsius=35.0,
            ndvi_vegetation_index=5.5,  # NDVI > 1.0 rejected
        )

    # 2. Extreme outlier observation (extreme cloudburst 999mm, scorching heat 58.0°C)
    service = RiskEngineService()
    extreme_obs = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=999.0,      # Extreme precipitation
        temperature_celsius=58.0,     # Extreme heat
        relative_humidity_pct=99.0,
        ndvi_vegetation_index=0.99,
    )

    result = asyncio.run(service.assess_borrower_risk(sample_borrower, extreme_obs, sample_baseline))

    # Trigger fired due to extreme excess precipitation breach
    assert result.trigger_fired is True
    assert result.recommended_action.action_type == TriggerActionType.RECOVERY_TOPUP
    # Risk score stays safely bounded within [0, 100]
    assert 0.0 <= result.risk_score <= 100.0


# =============================================================================
# 5. CONFIG-DRIVEN RECALIBRATION TEST
# =============================================================================

def test_config_recalibration_without_redeploy(tmp_path, sample_borrower, sample_baseline):
    """Verifies that thresholds are config-driven and update immediately when modified."""
    import json
    from risk_engine.config.loader import RiskEngineConfig

    custom_cfg = {
        "version": "test-override",
        "sectors": {
            "AGRI_ALLIED": {
                "rainfall_deficit_pct": -20.0,  # Relaxed trigger from -35% to -20%
                "excess_rainfall_percentile": 90.0,
                "deficit_action": {
                    "action_type": "EMI_DEFERRAL",
                    "relief_period_days": 45,
                    "policy_code": "POL-CUSTOM-AGRI"
                }
            }
        }
    }

    model_cfg = {
        "coefficients": {"rainfall_deficit_ratio": 2.0},
        "intercept": -1.5,
        "sector_weights": {"AGRI_ALLIED": 1.0}
    }

    t_file = tmp_path / "thresholds.json"
    m_file = tmp_path / "model_config.json"

    with open(t_file, "w") as f:
        json.dump(custom_cfg, f)
    with open(m_file, "w") as f:
        json.dump(model_cfg, f)

    config = RiskEngineConfig(thresholds_path=t_file, model_config_path=m_file)
    evaluator = RuleBasedTriggerEvaluator(config)

    # Test observation at -25% deficit (217.5mm vs 290mm)
    obs = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=217.5,
        temperature_celsius=33.5,
    )

    # Under standard config (-35%), this would NOT fire.
    # Under custom config (-20%), this MUST fire with 45 days relief.
    fired, _, action, _ = evaluator.evaluate(sample_borrower, obs, sample_baseline)
    assert fired is True
    assert action.relief_period_days == 45
    assert action.policy_code == "POL-CUSTOM-AGRI"


# =============================================================================
# 6. EXPLAINABILITY & TRANSPARENCY TEST
# =============================================================================

def test_explainable_ml_features_and_contributions(sample_borrower, sample_baseline):
    """Verifies that the ML model produces inspectable feature contributions and bounded score."""
    model = ExplainableMLZoningModel()

    obs = ClimateObservation(
        timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        location=sample_borrower.location,
        source=DataSourceType.NASA_POWER,
        precipitation_mm=100.0,
        temperature_celsius=38.0,
        ndvi_vegetation_index=0.45,
    )

    score, tier, contributions = model.predict_vulnerability(sample_borrower, obs, sample_baseline)

    assert 0.0 <= score <= 100.0
    assert tier in list(RiskTier)
    # Ensure key expected features are present in contributions breakdown
    assert "rainfall_deficit_ratio" in contributions
    assert "sector_vulnerability_weight" in contributions
    assert "credit_exposure_ratio" in contributions
    assert all(isinstance(v, float) for v in contributions.values())

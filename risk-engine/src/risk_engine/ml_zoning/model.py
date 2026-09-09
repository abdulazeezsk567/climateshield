"""Lightweight explainable ML microclimate vulnerability zoning model.

DECISION-SUPPORT NOTICE:
This model produces a calibrated vulnerability index on a continuous 0-100 scale.
It is strictly a decision-support heuristic designed to prioritize portfolio
monitoring and pre-emptive loan support. It does NOT claim or imply certainty
regarding individual borrower repayment outcomes or defaults.
"""

import math
from typing import Any, Dict, Optional, Tuple
from climateshield_shared.constants import RiskTier
from climateshield_shared.schemas.borrower import Borrower
from climateshield_shared.schemas.climate import ClimateObservation
from data_layer.baselines.interfaces import HistoricalClimateBaseline
from risk_engine.config.loader import RiskEngineConfig


class ExplainableMLZoningModel:
    """Calibrated, transparent linear-logistic scoring model for climate risk zoning.

    Features and weights are externalized in model_config.json to allow auditability
    and runtime recalibration without requiring redeployments.
    """

    def __init__(self, config: Optional[RiskEngineConfig] = None):
        self.config = config or RiskEngineConfig()

    def predict_vulnerability(
        self,
        borrower: Borrower,
        observation: ClimateObservation,
        baseline: HistoricalClimateBaseline,
    ) -> Tuple[float, RiskTier, Dict[str, float]]:
        """Compute continuous risk score, tier, and transparent feature contributions.

        Args:
            borrower: Target MSME borrower profile.
            observation: Current environmental observations.
            baseline: District historical climate baseline.

        Returns:
            Tuple of (risk_score_0_to_100, RiskTier, feature_contributions_dict).
        """
        model_cfg = self.config.model_config
        weights = model_cfg.get("coefficients", {})
        intercept = float(model_cfg.get("intercept", -1.80))
        sector_weights = model_cfg.get("sector_weights", {})

        # Extract normalized, bounded features
        features = self._extract_features(borrower, observation, baseline, sector_weights)

        # Compute transparent linear combination
        z = intercept
        contributions: Dict[str, float] = {}

        for feature_name, feature_val in features.items():
            w = float(weights.get(feature_name, 1.0))
            contrib = w * feature_val
            contributions[feature_name] = round(contrib, 3)
            z += contrib

        # Apply bounded logistic sigmoid activation
        # Clamped to avoid float overflow under extreme inputs
        z_clamped = max(-20.0, min(20.0, z))
        prob = 1.0 / (1.0 + math.exp(-z_clamped))
        risk_score = round(prob * 100.0, 2)

        # Categorize into risk tier
        bounds = model_cfg.get("scaling_bounds", {})
        mod_cutoff = float(bounds.get("moderate_risk_cutoff", 40.0))
        high_cutoff = float(bounds.get("high_risk_cutoff", 65.0))
        severe_cutoff = float(bounds.get("severe_risk_cutoff", 85.0))

        if risk_score >= severe_cutoff:
            tier = RiskTier.SEVERE
        elif risk_score >= high_cutoff:
            tier = RiskTier.HIGH
        elif risk_score >= mod_cutoff:
            tier = RiskTier.MODERATE
        else:
            tier = RiskTier.LOW

        return risk_score, tier, contributions

    def _extract_features(
        self,
        borrower: Borrower,
        observation: ClimateObservation,
        baseline: HistoricalClimateBaseline,
        sector_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """Derive normalized model input features."""
        # Feature 1: Rainfall deficit ratio [0.0, 1.0]
        avg_rain = baseline.avg_rainfall_mm
        curr_rain = max(0.0, observation.precipitation_mm)
        if avg_rain > 0.0 and curr_rain < avg_rain:
            rain_deficit = (avg_rain - curr_rain) / avg_rain
        else:
            rain_deficit = 0.0
        rain_deficit = max(0.0, min(1.0, rain_deficit))

        # Feature 2: Extreme rain ratio above 95th percentile [0.0, 3.0]
        p95 = baseline.rainfall_95th_percentile_mm
        if p95 > 0.0 and curr_rain > p95:
            extreme_rain = (curr_rain - p95) / p95
        else:
            extreme_rain = 0.0
        extreme_rain = max(0.0, min(3.0, extreme_rain))

        # Feature 3: Temperature anomaly above baseline max [0.0, 15.0]
        base_temp = baseline.avg_max_temp_celsius
        temp_delta = max(0.0, observation.temperature_celsius - base_temp)
        temp_anomaly_norm = min(1.0, temp_delta / 10.0)

        # Feature 4: Vegetation stress delta [0.0, 1.0]
        # Missing NDVI is treated as neutral (0.0)
        ndvi_stress = 0.0
        if (
            observation.ndvi_vegetation_index is not None
            and baseline.avg_ndvi_vegetation_index > 0.0
        ):
            base_ndvi = baseline.avg_ndvi_vegetation_index
            if observation.ndvi_vegetation_index < base_ndvi:
                ndvi_stress = (base_ndvi - observation.ndvi_vegetation_index) / base_ndvi
        ndvi_stress = max(0.0, min(1.0, ndvi_stress))

        # Feature 5: Sector vulnerability weighting [0.0, 1.0]
        sector_key = borrower.sector.value
        sector_vuln = float(sector_weights.get(sector_key, 0.50))

        # Feature 6: Credit exposure ratio relative to benchmark [0.0, 1.0]
        exposure_ratio = min(1.0, borrower.total_active_exposure / 500000.0)

        return {
            "rainfall_deficit_ratio": round(rain_deficit, 4),
            "extreme_rain_ratio": round(extreme_rain, 4),
            "temperature_anomaly_celsius": round(temp_anomaly_norm, 4),
            "vegetation_stress_delta": round(ndvi_stress, 4),
            "sector_vulnerability_weight": round(sector_vuln, 4),
            "credit_exposure_ratio": round(exposure_ratio, 4),
        }

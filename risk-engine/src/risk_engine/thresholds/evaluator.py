"""Rule-based parametric trigger evaluator."""

from typing import Any, Dict, Optional, Tuple
from climateshield_shared.constants import (
    ClimateHazardType,
    TriggerActionType,
)
from climateshield_shared.schemas.borrower import Borrower
from climateshield_shared.schemas.climate import ClimateObservation
from climateshield_shared.schemas.trigger import TriggerActionProposal
from data_layer.baselines.interfaces import HistoricalClimateBaseline
from risk_engine.config.loader import RiskEngineConfig


class RuleBasedTriggerEvaluator:
    """Evaluates deterministic sector-specific parametric trigger thresholds.

    Relies entirely on externalized threshold configurations loaded via RiskEngineConfig.
    Produces decision-support indicators rather than assertions of certainty.
    """

    def __init__(self, config: Optional[RiskEngineConfig] = None):
        self.config = config or RiskEngineConfig()

    def evaluate(
        self,
        borrower: Borrower,
        observation: ClimateObservation,
        baseline: HistoricalClimateBaseline,
    ) -> Tuple[bool, Optional[str], Optional[TriggerActionProposal], Optional[ClimateHazardType]]:
        """Evaluate climate deviation against sector-specific configured thresholds.

        Args:
            borrower: MSME borrower profile containing sector and exposure details.
            observation: Current meteorological and remote sensing observation.
            baseline: Historical multi-year baseline for the borrower's district.

        Returns:
            Tuple of (trigger_fired, trigger_reason, recommended_action, primary_hazard).
        """
        sector_key = borrower.sector.value
        thresholds = self.config.get_sector_threshold(sector_key)

        # 1. Compute rainfall deviation percentage
        avg_rain = baseline.avg_rainfall_mm
        curr_rain = max(0.0, observation.precipitation_mm)

        if avg_rain > 0.0:
            rainfall_deviation_pct = ((curr_rain - avg_rain) / avg_rain) * 100.0
        else:
            rainfall_deviation_pct = 0.0

        deficit_threshold = float(thresholds.get("rainfall_deficit_pct", -40.0))
        excess_p95 = baseline.rainfall_95th_percentile_mm

        # 2. Check NDVI vegetation stress if available
        ndvi_stress_pct = None
        if (
            observation.ndvi_vegetation_index is not None
            and baseline.avg_ndvi_vegetation_index > 0.0
        ):
            ndvi_stress_pct = (
                (observation.ndvi_vegetation_index - baseline.avg_ndvi_vegetation_index)
                / baseline.avg_ndvi_vegetation_index
            ) * 100.0

        ndvi_threshold = float(thresholds.get("ndvi_vegetation_stress_pct", -30.0))

        # Check Threshold Breaches:

        # Scenario A: Severe Rainfall Deficit (Drought Shock)
        if rainfall_deviation_pct <= deficit_threshold:
            action_spec = thresholds.get("deficit_action", {})
            action = TriggerActionProposal(
                action_type=TriggerActionType(action_spec.get("action_type", "EMI_DEFERRAL")),
                relief_period_days=action_spec.get("relief_period_days", 30),
                topup_amount=None,
                reasoning=(
                    f"Rainfall deficit of {rainfall_deviation_pct:.1f}% crossed sector '{sector_key}' "
                    f"trigger threshold ({deficit_threshold:.1f}%). Pre-emptive relief recommended."
                ),
                policy_code=action_spec.get("policy_code", "POL-DEFICIT-30D"),
            )
            reason = (
                f"Rainfall deficit of {rainfall_deviation_pct:.1f}% below monthly baseline "
                f"({avg_rain:.1f}mm), breaching {deficit_threshold:.1f}% threshold."
            )
            return True, reason, action, ClimateHazardType.DROUGHT_DEFICIT

        # Scenario B: Extreme Precipitation (Flash Flood / Waterlogging Shock)
        if curr_rain >= excess_p95 and excess_p95 > 0.0:
            action_spec = thresholds.get("excess_action", {})
            topup_pct = float(action_spec.get("topup_percentage", 0.10))
            topup_amount = round(borrower.total_active_exposure * topup_pct, 2)

            action = TriggerActionProposal(
                action_type=TriggerActionType(action_spec.get("action_type", "RECOVERY_TOPUP")),
                relief_period_days=None,
                topup_amount=topup_amount,
                reasoning=(
                    f"Extreme precipitation of {curr_rain:.1f}mm breached district 95th percentile "
                    f"({excess_p95:.1f}mm). Pre-emptive recovery credit line recommended."
                ),
                policy_code=action_spec.get("policy_code", "POL-EXCESS-TOPUP"),
            )
            reason = (
                f"Observed precipitation ({curr_rain:.1f}mm) exceeded 95th percentile "
                f"baseline threshold ({excess_p95:.1f}mm)."
            )
            return True, reason, action, ClimateHazardType.EXCESS_RAINFALL

        # Scenario C: Severe Vegetation Stress (Crop / Fodder Failure)
        if ndvi_stress_pct is not None and ndvi_stress_pct <= ndvi_threshold:
            action = TriggerActionProposal(
                action_type=TriggerActionType.EMI_DEFERRAL,
                relief_period_days=30,
                topup_amount=None,
                reasoning=(
                    f"Satellite NDVI reduction of {ndvi_stress_pct:.1f}% crossed sector threshold "
                    f"({ndvi_threshold:.1f}%). Indicating severe vegetative stress."
                ),
                policy_code="POL-VEGETATION-STRESS-30D",
            )
            reason = (
                f"NDVI drop of {ndvi_stress_pct:.1f}% below baseline ({baseline.avg_ndvi_vegetation_index:.2f}), "
                f"breaching {ndvi_threshold:.1f}% threshold."
            )
            return True, reason, action, ClimateHazardType.VEGETATION_STRESS

        # Scenario D: Normal Operating Range
        return (
            False,
            "Environmental telemetry within configured historical tolerance bounds.",
            None,
            None,
        )

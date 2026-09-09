"""ClimateShield Risk & Trigger Engine Service.

===============================================================================
BASIS-RISK MITIGATION ARCHITECTURE NOTE:
===============================================================================
In parametric climate finance and NBFC micro-lending, "basis risk" is the
fundamental discrepancy between an automated index/trigger firing and the
actual economic loss experienced by an individual borrower:
  1. False Positive (Type I Basis Risk): The trigger fires (e.g. gridded
     weather station indicates rainfall deficit), but a specific borrower had
     private tube-well irrigation, crop diversification, or elevated premises,
     experiencing no repayment distress.
  2. False Negative (Type II Basis Risk): The trigger does not fire (regional
     metrics stay slightly below the 95th percentile), yet severe localized
     waterlogging or pest outbreaks devastate an MSME cluster.

How ClimateShield Reductively Mitigates Basis Risk:
-------------------------------------------------------------------------------
1. Multi-Sensor Data Triangulation:
   Rather than relying exclusively on a single distant weather station, the
   engine correlates atmospheric telemetry (rainfall, heat degree days) with
   surface vegetative reflectance (satellite NDVI). A drought trigger requires
   coherent environmental corroboration.

2. Sector Sensitivity Stratification:
   A blanket weather anomaly is not applied uniformly across disparate
   commercial enterprises. An agricultural borrower (AGRI_ALLIED) has a lower
   drought threshold (-35%), whereas an urban textile handloom weaver
   (HANDLOOMS_TEXTILES) has a higher threshold (-55%), preventing false relief
   disbursements to sectors insulated from immediate moisture deficits.

3. Exposure & Loan Outcome Contextualization:
   The ML zoning model integrates active credit balance and remaining loan
   tenure into the continuous vulnerability index, ensuring that pre-emptive
   moratoriums prioritize borrowers with high active debt servicing burdens.

4. Basis-Risk Quality Caveat Flags & Human-in-the-Loop Audit:
   When telemetry is incomplete (e.g. cloud-obscured NDVI) or inputs sit near
   boundary thresholds, the service tags the output with `basis_risk_flags`
   (e.g. "MISSING_SATELLITE_NDVI_CONFIRMATION", "BOUNDARY_THRESHOLD_PROXIMITY").
   This explicitly flags cases requiring NBFC field officer inspection rather
   than blind automated execution.

5. Decision-Support Stance:
   The outputs are framed and documented as vulnerability risk scores and
   pre-emptive policy recommendations—never assertions of deterministic
   individual default certainty.
===============================================================================
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional

from climateshield_shared.schemas.borrower import Borrower, BorrowerSector
from climateshield_shared.schemas.climate import ClimateObservation
from climateshield_shared.schemas.trigger import BorrowerRiskOutput
from data_layer import DataLayerService, get_data_layer_service
from data_layer.baselines.interfaces import HistoricalClimateBaseline
from risk_engine.config.loader import RiskEngineConfig
from risk_engine.ml_zoning.model import ExplainableMLZoningModel
from risk_engine.thresholds.evaluator import RuleBasedTriggerEvaluator

logger = logging.getLogger(__name__)


class RiskEngineService:
    """Consumes Data Layer telemetry through its public interface to evaluate risk.

    Provides combined risk outputs synthesizing deterministic threshold checks
    with explainable continuous ML vulnerability scores.
    """

    def __init__(
        self,
        data_layer: Optional[DataLayerService] = None,
        config: Optional[RiskEngineConfig] = None,
    ):
        # Consume Data Layer strictly via its public service interface
        self._data_layer = data_layer or get_data_layer_service()
        self._config = config or RiskEngineConfig()
        self._evaluator = RuleBasedTriggerEvaluator(self._config)
        self._ml_model = ExplainableMLZoningModel(self._config)

    @property
    def config(self) -> RiskEngineConfig:
        """Public configuration instance."""
        return self._config

    async def assess_borrower_risk(
        self,
        borrower: Borrower,
        observation: ClimateObservation,
        baseline: HistoricalClimateBaseline,
    ) -> BorrowerRiskOutput:
        """Evaluate combined climate risk and parametric trigger for a borrower.

        Args:
            borrower: MSME borrower record.
            observation: Current climate observation for borrower's location.
            baseline: District historical baseline for the observation month.

        Returns:
            BorrowerRiskOutput record conforming to the cross-service schema.
        """
        # 1. Sanitize & clamp input extremes to guard against adversarial/malformed values
        sanitized_obs = self._sanitize_observation(observation)

        # 2. Track basis risk caveats
        basis_flags: List[str] = []
        if observation.ndvi_vegetation_index is None:
            basis_flags.append("MISSING_SATELLITE_NDVI_CONFIRMATION")
        if observation.relative_humidity_pct is None:
            basis_flags.append("UNCONFIRMED_HUMIDITY_TELEMETRY")

        # 3. Rule-based threshold check
        trigger_fired, trigger_reason, action, _ = self._evaluator.evaluate(
            borrower, sanitized_obs, baseline
        )

        # 4. Check for boundary proximity (within 3% of trigger threshold)
        if self._is_near_boundary(borrower, sanitized_obs, baseline):
            basis_flags.append("BOUNDARY_THRESHOLD_PROXIMITY")

        # 5. Continuous ML zoning vulnerability prediction
        risk_score, _, contributions = self._ml_model.predict_vulnerability(
            borrower, sanitized_obs, baseline
        )

        # If trigger fired but ML score is moderate, note divergence in basis flags
        if trigger_fired and risk_score < 40.0:
            basis_flags.append("ANOMALY_TRIGGER_DIVERGES_FROM_LOW_ML_ZONING")
        elif not trigger_fired and risk_score >= 70.0:
            basis_flags.append("ELEVATED_ML_VULNERABILITY_WITHOUT_PARAMETRIC_BREACH")

        return BorrowerRiskOutput(
            borrower_id=borrower.borrower_id,
            risk_score=risk_score,
            trigger_fired=trigger_fired,
            trigger_reason=trigger_reason,
            recommended_action=action,
            basis_risk_flags=basis_flags,
            evaluated_at=datetime.now(timezone.utc),
        )

    async def assess_district_portfolio(
        self,
        district_id: str,
        observation: ClimateObservation,
        sector: Optional[BorrowerSector] = None,
    ) -> List[BorrowerRiskOutput]:
        """Assess all active MSME borrowers in a district under observed climate conditions.

        Consumes data from Data Layer's public methods:
        - `get_district_baseline(district_id, month)`
        - `list_borrowers(district_id, sector)`
        """
        month = observation.timestamp.month
        baseline = await self._data_layer.get_district_baseline(district_id, month)
        borrowers = await self._data_layer.list_borrowers(district_id, sector)

        results: List[BorrowerRiskOutput] = []
        for b in borrowers:
            out = await self.assess_borrower_risk(b, observation, baseline)
            results.append(out)

        return results

    def _sanitize_observation(self, obs: ClimateObservation) -> ClimateObservation:
        """Adversarial input guard: clamps negative or implausible telemetry values."""
        # Create a copy with bounded values
        clamped_precip = max(0.0, min(1000.0, obs.precipitation_mm))
        clamped_temp = max(-30.0, min(65.0, obs.temperature_celsius))
        clamped_ndvi = (
            max(-1.0, min(1.0, obs.ndvi_vegetation_index))
            if obs.ndvi_vegetation_index is not None
            else None
        )

        return ClimateObservation(
            timestamp=obs.timestamp,
            location=obs.location,
            source=obs.source,
            precipitation_mm=clamped_precip,
            temperature_celsius=clamped_temp,
            relative_humidity_pct=obs.relative_humidity_pct,
            wind_speed_kmh=obs.wind_speed_kmh,
            ndvi_vegetation_index=clamped_ndvi,
        )

    def _is_near_boundary(
        self,
        borrower: Borrower,
        obs: ClimateObservation,
        baseline: HistoricalClimateBaseline,
    ) -> bool:
        """Flag when a measurement is within 3.0% of a sector trigger boundary."""
        thresholds = self._config.get_sector_threshold(borrower.sector.value)
        deficit_thresh = float(thresholds.get("rainfall_deficit_pct", -40.0))

        if baseline.avg_rainfall_mm > 0.0:
            dev_pct = ((obs.precipitation_mm - baseline.avg_rainfall_mm) / baseline.avg_rainfall_mm) * 100.0
            if abs(dev_pct - deficit_thresh) <= 3.0:
                return True

        if baseline.rainfall_95th_percentile_mm > 0.0:
            diff_p95 = abs(obs.precipitation_mm - baseline.rainfall_95th_percentile_mm)
            if diff_p95 <= (baseline.rainfall_95th_percentile_mm * 0.03):
                return True

        return False

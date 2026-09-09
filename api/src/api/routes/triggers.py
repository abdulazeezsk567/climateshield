"""Parametric trigger evaluation and interactive simulation endpoints."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from climateshield_shared.constants import ClimateHazardType, LMSExecutionStatus, RiskTier
from climateshield_shared.schemas.climate import ClimateObservation, DataSourceType
from climateshield_shared.schemas.trigger import TriggerActionProposal, TriggerEvent
from api.core.dependencies import UserContext, get_data_layer, get_integration, get_risk_engine, require_role
from data_layer import DataLayerService
from data_layer.exceptions import RecordNotFoundError
from integration_layer import IntegrationService
from risk_engine import RiskEngineService

router = APIRouter(prefix="/triggers", tags=["Trigger Simulations & Policy Interventions"])


class SimulationRequest(BaseModel):
    """Payload to inject an on-demand climate anomaly scenario for live demonstration."""
    district: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z\s-]+$",
        description="Target administrative district to simulate shock in",
    )
    hazard_type: ClimateHazardType = Field(..., description="Climate hazard scenario type")
    intensity_multiplier: float = Field(
        default=1.5,
        ge=0.1,
        le=5.0,
        description="Shock intensity multiplier against historical baseline",
    )
    custom_rainfall_mm: Optional[float] = Field(None, ge=0.0, description="Override absolute rainfall measurement in mm")
    custom_temperature_celsius: Optional[float] = Field(None, ge=-10.0, le=60.0, description="Override temperature in °C")
    custom_ndvi_vegetation_index: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Override vegetation NDVI index")


class SimulationResultResponse(BaseModel):
    """Structured outcome of a parametric trigger simulation run."""
    district: str
    hazard_type: ClimateHazardType
    total_borrowers_evaluated: int
    triggers_activated: int
    affected_borrower_ids: List[str]
    generated_lms_actions_count: int
    total_relief_exposure: float
    sample_trigger_event: Optional[TriggerEvent] = None
    simulation_timestamp: datetime


@router.post(
    "/simulate",
    response_model=SimulationResultResponse,
    summary="Inject Climate Anomaly Simulation Scenario",
    description="Simulates a climate shock in a target district (drought, extreme rainfall, or heatwave), evaluates borrower trigger rules via the Risk Engine, automatically dispatches mock LMS loan adjustments to the Integration Layer, and records an immutable audit trail.",
)
async def simulate_trigger_scenario(
    payload: SimulationRequest,
    current_user: UserContext = Depends(require_role("credit_team")),
    data_layer: DataLayerService = Depends(get_data_layer),
    risk_engine: RiskEngineService = Depends(get_risk_engine),
    integration: IntegrationService = Depends(get_integration),
) -> SimulationResultResponse:
    """Execute end-to-end parametric simulation and downstream action dispatch."""
    dist = payload.district.strip().upper()
    now = datetime.now(timezone.utc)

    # 1. Fetch district baseline and borrower portfolio
    baseline = await data_layer.get_district_baseline(dist, now.month)
    borrowers = await data_layer.list_borrowers(district_id=dist)

    if not borrowers:
        raise RecordNotFoundError(f"No active MSME borrowers found in district '{dist}' to simulate.")

    # 2. Synthesize shock observation according to scenario parameters
    rep = borrowers[0]
    if payload.hazard_type == ClimateHazardType.DROUGHT_DEFICIT:
        precip = (
            payload.custom_rainfall_mm
            if payload.custom_rainfall_mm is not None
            else max(0.0, baseline.avg_rainfall_mm * (1.0 - (0.45 * payload.intensity_multiplier)))
        )
        temp = payload.custom_temperature_celsius or (baseline.avg_max_temp_celsius + 3.0)
        ndvi = payload.custom_ndvi_vegetation_index or max(0.1, baseline.avg_ndvi_vegetation_index - 0.25)
    elif payload.hazard_type == ClimateHazardType.EXCESS_RAINFALL:
        precip = (
            payload.custom_rainfall_mm
            if payload.custom_rainfall_mm is not None
            else baseline.rainfall_95th_percentile_mm * payload.intensity_multiplier
        )
        temp = payload.custom_temperature_celsius or (baseline.avg_max_temp_celsius - 4.0)
        ndvi = payload.custom_ndvi_vegetation_index or baseline.avg_ndvi_vegetation_index
    else:  # VEGETATION_STRESS or HEATWAVE
        precip = payload.custom_rainfall_mm or (baseline.avg_rainfall_mm * 0.5)
        temp = payload.custom_temperature_celsius or (baseline.avg_max_temp_celsius + 5.0)
        ndvi = payload.custom_ndvi_vegetation_index or (baseline.avg_ndvi_vegetation_index * 0.5)

    simulated_obs = ClimateObservation(
        timestamp=now,
        location=rep.location,
        source=DataSourceType.SYNTHETIC_SIMULATOR,
        precipitation_mm=round(precip, 2),
        temperature_celsius=round(temp, 1),
        relative_humidity_pct=85.0 if precip > 100 else 40.0,
        wind_speed_kmh=25.0,
        ndvi_vegetation_index=round(ndvi, 3),
    )

    # 3. Evaluate each borrower in the district
    from climateshield_shared.telemetry import get_metrics_registry
    metrics = get_metrics_registry()
    metrics.increment_triggers_evaluated(payload.hazard_type.value, payload.district)

    triggered_borrowers = []
    lms_actions_executed = 0
    total_relief_exposure = 0.0
    primary_proposal: Optional[TriggerActionProposal] = None

    for b in borrowers:
        res = await risk_engine.assess_borrower_risk(b, simulated_obs, baseline)
        if res.trigger_fired and res.recommended_action:
            triggered_borrowers.append(b.borrower_id)
            total_relief_exposure += b.total_active_exposure

            if not primary_proposal:
                primary_proposal = res.recommended_action

            # Dispatch simulated LMS action for active loans
            for loan in b.active_loans:
                lms_resp = await integration.execute_loan_intervention(
                    borrower_id=b.borrower_id,
                    loan_id=loan.loan_id,
                    action=res.recommended_action,
                    trigger_id=f"TRIG-SIM-{dist}",
                    actor=f"user:{current_user.user_id}",
                )
                lms_actions_executed += 1
                metrics.increment_interventions_dispatched(res.recommended_action.action_type.value)

            # Dispatch simulated alert
            await integration.send_borrower_relief_alert(
                borrower_id=b.borrower_id,
                message_text=f"ClimateShield Advisory: Proactive climate relief ({res.recommended_action.action_type.value}) sanctioned for district {dist}.",
                actor=f"user:{current_user.user_id}",
            )

    # 4. Formulate TriggerEvent record if any triggers activated
    sample_trigger = None
    if triggered_borrowers and primary_proposal:
        metrics.increment_triggers_fired(payload.hazard_type.value, payload.district)
        trig_id = f"TRIG-{uuid.uuid4().hex[:8].upper()}"
        sample_trigger = TriggerEvent(
            trigger_id=trig_id,
            triggered_at=now,
            district=dist,
            hazard_type=payload.hazard_type,
            severity=RiskTier.HIGH if len(triggered_borrowers) > len(borrowers) // 2 else RiskTier.MODERATE,
            affected_borrower_ids=triggered_borrowers,
            recommended_action=primary_proposal,
            execution_status=LMSExecutionStatus.SIMULATED_SUCCESS,
        )
        # Store in audit registry
        await integration.record_trigger_event(sample_trigger, actor=f"user:{current_user.user_id}")

    return SimulationResultResponse(
        district=dist,
        hazard_type=payload.hazard_type,
        total_borrowers_evaluated=len(borrowers),
        triggers_activated=len(triggered_borrowers),
        affected_borrower_ids=triggered_borrowers,
        generated_lms_actions_count=lms_actions_executed,
        total_relief_exposure=round(total_relief_exposure, 2),
        sample_trigger_event=sample_trigger,
        simulation_timestamp=now,
    )


@router.get(
    "/active",
    response_model=List[TriggerEvent],
    summary="List Active Parametric Triggers",
    description="Returns all active or simulated parametric trigger events registered across the portfolio.",
)
async def list_active_triggers(
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    integration: IntegrationService = Depends(get_integration),
) -> List[TriggerEvent]:
    """Retrieve all recorded trigger events."""
    return await integration.list_active_triggers()

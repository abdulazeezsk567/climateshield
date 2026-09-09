"""Borrower risk analytics and evaluation endpoints."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field

from climateshield_shared.constants import RiskTier
from climateshield_shared.schemas.borrower import Borrower, BorrowerSector
from climateshield_shared.schemas.trigger import BorrowerRiskOutput
from api.core.dependencies import UserContext, get_data_layer, get_risk_engine, require_role
from api.core.pagination import PaginatedResponse, paginate_items
from data_layer import DataLayerService
from data_layer.exceptions import RecordNotFoundError
from risk_engine import RiskEngineService

router = APIRouter(prefix="/risk", tags=["Borrower Risk Intelligence"])


class BorrowerRiskSummary(BaseModel):
    """Summarized risk scorecard for list display."""
    borrower_id: str
    anonymized_alias: str
    district: str
    sector: BorrowerSector
    total_active_exposure: float
    risk_score: float
    risk_tier: RiskTier
    trigger_fired: bool
    trigger_reason: Optional[str] = None
    basis_risk_flags: List[str] = Field(default_factory=list)


class DetailedBorrowerRiskScorecard(BaseModel):
    """Full borrower risk scorecard with loan breakdown and telemetry context."""
    borrower: Borrower
    risk_assessment: BorrowerRiskOutput
    district_monthly_baseline: Dict[str, float]
    latest_telemetry: Dict[str, float]
    model_feature_contributions: Dict[str, float]


@router.get(
    "/borrowers",
    response_model=PaginatedResponse[BorrowerRiskSummary],
    summary="List Borrower Risk Scorecards (Paginated)",
    description="Returns a paginated list of MSME borrowers with their computed climate risk scores, filterable by district, sector, and minimum risk score.",
)
async def list_borrower_risks(
    district: Optional[str] = Query(None, description="Filter by administrative district"),
    sector: Optional[BorrowerSector] = Query(None, description="Filter by MSME industry sector"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Filter borrowers with risk score >= threshold"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1 to 100)"),
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    data_layer: DataLayerService = Depends(get_data_layer),
    risk_engine: RiskEngineService = Depends(get_risk_engine),
) -> PaginatedResponse[BorrowerRiskSummary]:
    """Retrieve paginated borrower risk scores with optional multi-attribute filters."""
    borrowers = await data_layer.list_borrowers(district_id=district, sector=sector)
    now = datetime.now(timezone.utc)

    summaries: List[BorrowerRiskSummary] = []

    # Cache district baseline and observation per district to avoid repeated calls
    district_cache: Dict[str, tuple] = {}

    for b in borrowers:
        dist = b.location.district.upper()
        if dist not in district_cache:
            try:
                base = await data_layer.get_district_baseline(dist, now.month)
                obs_list = await data_layer.get_weather_observations(
                    latitude=b.location.latitude,
                    longitude=b.location.longitude,
                    start_date=now.date(),
                    end_date=now.date(),
                    provider="synthetic",
                    district_name=dist,
                    state_name=b.location.state,
                )
                district_cache[dist] = (base, obs_list[0] if obs_list else None)
            except Exception:
                district_cache[dist] = (None, None)

        base, obs = district_cache[dist]
        if base and obs:
            risk_out = await risk_engine.assess_borrower_risk(b, obs, base)
            score = risk_out.risk_score
            fired = risk_out.trigger_fired
            reason = risk_out.trigger_reason
            flags = risk_out.basis_risk_flags
        else:
            score = 30.0
            fired = False
            reason = None
            flags = ["MISSING_HISTORICAL_BASELINE"]

        if score >= 85.0:
            tier = RiskTier.SEVERE
        elif score >= 65.0:
            tier = RiskTier.HIGH
        elif score >= 40.0:
            tier = RiskTier.MODERATE
        else:
            tier = RiskTier.LOW

        # Apply minimum risk filter
        if min_risk_score is not None and score < min_risk_score:
            continue

        summaries.append(
            BorrowerRiskSummary(
                borrower_id=b.borrower_id,
                anonymized_alias=b.anonymized_alias,
                district=b.location.district,
                sector=b.sector,
                total_active_exposure=b.total_active_exposure,
                risk_score=score,
                risk_tier=tier,
                trigger_fired=fired,
                trigger_reason=reason,
                basis_risk_flags=flags,
            )
        )

    return paginate_items(summaries, page=page, page_size=page_size)


@router.get(
    "/borrowers/{borrower_id}",
    response_model=DetailedBorrowerRiskScorecard,
    summary="Get Detailed Borrower Risk Scorecard",
    description="Retrieve comprehensive risk analysis, loan account schedules, and explainable feature contributions for a specific borrower.",
)
async def get_borrower_risk_detail(
    borrower_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{3,50}$", description="Unique borrower ID"),
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    data_layer: DataLayerService = Depends(get_data_layer),
    risk_engine: RiskEngineService = Depends(get_risk_engine),
) -> DetailedBorrowerRiskScorecard:
    """Fetch granular climate risk scorecard for a single borrower account."""
    borrower = await data_layer.get_borrower(borrower_id)
    if not borrower:
        raise RecordNotFoundError(f"Borrower with ID '{borrower_id}' was not found.")

    dist = borrower.location.district.upper()
    now = datetime.now(timezone.utc)

    baseline = await data_layer.get_district_baseline(dist, now.month)
    obs_list = await data_layer.get_weather_observations(
        latitude=borrower.location.latitude,
        longitude=borrower.location.longitude,
        start_date=now.date(),
        end_date=now.date(),
        provider="synthetic",
        district_name=dist,
        state_name=borrower.location.state,
    )
    obs = obs_list[0]

    risk_out = await risk_engine.assess_borrower_risk(borrower, obs, baseline)
    _, _, contributions = risk_engine._ml_model.predict_vulnerability(borrower, obs, baseline)

    return DetailedBorrowerRiskScorecard(
        borrower=borrower,
        risk_assessment=risk_out,
        district_monthly_baseline={
            "avg_rainfall_mm": baseline.avg_rainfall_mm,
            "rainfall_std_dev_mm": baseline.rainfall_std_dev_mm,
            "rainfall_95th_percentile_mm": baseline.rainfall_95th_percentile_mm,
            "avg_max_temp_celsius": baseline.avg_max_temp_celsius,
            "avg_ndvi_vegetation_index": baseline.avg_ndvi_vegetation_index,
        },
        latest_telemetry={
            "precipitation_mm": obs.precipitation_mm,
            "temperature_celsius": obs.temperature_celsius,
            "relative_humidity_pct": obs.relative_humidity_pct or 0.0,
            "wind_speed_kmh": obs.wind_speed_kmh or 0.0,
            "ndvi_vegetation_index": obs.ndvi_vegetation_index or 0.0,
        },
        model_feature_contributions=contributions,
    )

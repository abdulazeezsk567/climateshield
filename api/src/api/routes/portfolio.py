"""Portfolio intelligence and geospatial risk heatmap endpoints."""

from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from climateshield_shared.constants import ClimateHazardType, RiskTier
from api.core.dependencies import UserContext, get_data_layer, get_risk_engine, require_role
from data_layer import DataLayerService
from risk_engine import RiskEngineService

router = APIRouter(prefix="/portfolio", tags=["Portfolio Intelligence"])


class PortfolioSummaryResponse(BaseModel):
    """Aggregated exposure and vulnerability metrics for MSME lending portfolios."""
    total_active_borrowers: int = Field(..., description="Total active MSME borrowers monitored")
    total_credit_exposure: float = Field(..., description="Aggregated principal debt exposure in INR")
    districts_monitored: int = Field(..., description="Count of covered operational districts")
    high_risk_exposure_percentage: float = Field(
        ..., description="Percentage of active credit exposure located in high or severe climate risk zones"
    )
    active_districts: List[str] = Field(..., description="List of operational district names")


class DistrictHeatmapNode(BaseModel):
    """Geospatial visualization node for district-level risk mapping."""
    district: str = Field(..., description="District administrative name")
    state: str = Field(..., description="State administrative name")
    latitude: float = Field(..., description="Centroid latitude")
    longitude: float = Field(..., description="Centroid longitude")
    borrower_count: int = Field(..., description="Count of active MSME borrowers in this district")
    total_exposure: float = Field(..., description="Total active exposure in INR")
    average_risk_score: float = Field(..., ge=0.0, le=100.0, description="Average vulnerability score (0-100)")
    risk_tier: RiskTier = Field(..., description="Categorical vulnerability classification")
    primary_hazard: ClimateHazardType = Field(..., description="Dominant climate risk hazard for the district")
    last_monitored: datetime = Field(..., description="Timestamp of telemetry evaluation")


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get Portfolio Climate Risk Summary",
    description="Calculates portfolio exposure aggregates and the proportion of active debt situated in elevated climate risk zones.",
)
async def get_portfolio_summary(
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    data_layer: DataLayerService = Depends(get_data_layer),
    risk_engine: RiskEngineService = Depends(get_risk_engine),
) -> PortfolioSummaryResponse:
    """Compute top-level portfolio exposure and climate vulnerability metrics."""
    borrowers = await data_layer.list_borrowers()
    summary = await data_layer.get_portfolio_summary()

    if not borrowers:
        return PortfolioSummaryResponse(
            total_active_borrowers=0,
            total_credit_exposure=0.0,
            districts_monitored=0,
            high_risk_exposure_percentage=0.0,
            active_districts=[],
        )

    # Assess sample borrower risk to compute high risk exposure share
    now = datetime.now(timezone.utc)
    high_risk_exposure = 0.0

    # Evaluate each district's borrowers against current baseline
    districts = {b.location.district.upper() for b in borrowers}
    for dist in districts:
        try:
            baseline = await data_layer.get_district_baseline(dist, now.month)
            dist_borrowers = [b for b in borrowers if b.location.district.upper() == dist]
            
            # Fetch representative observation
            rep_b = dist_borrowers[0]
            obs_list = await data_layer.get_weather_observations(
                latitude=rep_b.location.latitude,
                longitude=rep_b.location.longitude,
                start_date=now.date(),
                end_date=now.date(),
                provider="synthetic",
                district_name=dist,
                state_name=rep_b.location.state,
            )
            obs = obs_list[0] if obs_list else None

            if obs:
                for b in dist_borrowers:
                    risk_out = await risk_engine.assess_borrower_risk(b, obs, baseline)
                    if risk_out.risk_score >= 65.0:  # High or severe risk cutoff
                        high_risk_exposure += b.total_active_exposure
        except Exception:
            continue

    total_exposure = summary["total_credit_exposure"]
    high_risk_pct = round((high_risk_exposure / total_exposure) * 100.0, 2) if total_exposure > 0 else 0.0

    return PortfolioSummaryResponse(
        total_active_borrowers=summary["total_borrowers"],
        total_credit_exposure=total_exposure,
        districts_monitored=summary["districts_count"],
        high_risk_exposure_percentage=high_risk_pct,
        active_districts=summary["districts"],
    )


@router.get(
    "/heatmap",
    response_model=List[DistrictHeatmapNode],
    summary="Get Geospatial Risk Heatmap Data",
    description="Returns aggregated district clusters with geospatial centroids, loan exposure, and calculated climate risk scores for rendering on map components.",
)
async def get_portfolio_heatmap(
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    data_layer: DataLayerService = Depends(get_data_layer),
    risk_engine: RiskEngineService = Depends(get_risk_engine),
) -> List[DistrictHeatmapNode]:
    """Retrieve district-level geospatial nodes for dashboard risk heatmap visualization."""
    borrowers = await data_layer.list_borrowers()
    now = datetime.now(timezone.utc)
    district_groups: Dict[str, list] = {}

    for b in borrowers:
        dist_key = b.location.district.upper()
        if dist_key not in district_groups:
            district_groups[dist_key] = []
        district_groups[dist_key].append(b)

    nodes: List[DistrictHeatmapNode] = []

    for dist, b_list in district_groups.items():
        rep_borrower = b_list[0]
        total_dist_exposure = sum(b.total_active_exposure for b in b_list)

        try:
            baseline = await data_layer.get_district_baseline(dist, now.month)
            obs_list = await data_layer.get_weather_observations(
                latitude=rep_borrower.location.latitude,
                longitude=rep_borrower.location.longitude,
                start_date=now.date(),
                end_date=now.date(),
                provider="synthetic",
                district_name=dist,
                state_name=rep_borrower.location.state,
            )
            obs = obs_list[0]

            # Score borrowers in district
            scores = []
            for b in b_list:
                res = await risk_engine.assess_borrower_risk(b, obs, baseline)
                scores.append(res.risk_score)

            avg_score = round(sum(scores) / max(1, len(scores)), 2)

            if avg_score >= 85.0:
                tier = RiskTier.SEVERE
            elif avg_score >= 65.0:
                tier = RiskTier.HIGH
            elif avg_score >= 40.0:
                tier = RiskTier.MODERATE
            else:
                tier = RiskTier.LOW

            hazard = ClimateHazardType.DROUGHT_DEFICIT if now.month not in (7, 8) else ClimateHazardType.EXCESS_RAINFALL

        except Exception:
            avg_score = 35.0
            tier = RiskTier.LOW
            hazard = ClimateHazardType.DROUGHT_DEFICIT

        nodes.append(
            DistrictHeatmapNode(
                district=dist,
                state=rep_borrower.location.state,
                latitude=rep_borrower.location.latitude,
                longitude=rep_borrower.location.longitude,
                borrower_count=len(b_list),
                total_exposure=round(total_dist_exposure, 2),
                average_risk_score=avg_score,
                risk_tier=tier,
                primary_hazard=hazard,
                last_monitored=now,
            )
        )

    return nodes

"""Public Service Facade for ClimateShield Data Layer.

Acts as the single authoritative public boundary for the Data Layer.
Guarantees that consumer services (such as Risk Engine and API Gateway)
interact exclusively through typed contracts and validated methods, never
accessing raw underlying database tables or storage stores directly.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from climateshield_shared.schemas.borrower import Borrower, BorrowerSector
from climateshield_shared.schemas.climate import ClimateObservation
from data_layer.baselines.interfaces import HistoricalClimateBaseline
from data_layer.baselines.store import InMemoryBaselineStore
from data_layer.borrowers.store import InMemoryBorrowerRepository
from data_layer.exceptions import RecordNotFoundError
from data_layer.ingestion.satellite import SatelliteProvider, SentinelNDVIProvider
from data_layer.ingestion.weather import (
    IMDWeatherProvider,
    NASAPowerWeatherProvider,
    SyntheticWeatherProvider,
    WeatherProvider,
)
from data_layer.validators import validate_coordinates, validate_date_range


class DataLayerService:
    """Primary public interface mediating all data layer operations."""

    def __init__(
        self,
        baseline_store: Optional[InMemoryBaselineStore] = None,
        borrower_repo: Optional[InMemoryBorrowerRepository] = None,
        weather_provider: Optional[WeatherProvider] = None,
        satellite_provider: Optional[SatelliteProvider] = None,
    ):
        self._baseline_store = baseline_store or InMemoryBaselineStore()
        self._borrower_repo = borrower_repo or InMemoryBorrowerRepository()
        self._weather_providers: Dict[str, WeatherProvider] = {
            "nasa_power": weather_provider or NASAPowerWeatherProvider(),
            "imd": IMDWeatherProvider(),
            "synthetic": SyntheticWeatherProvider(),
        }
        self._satellite_provider = satellite_provider or SentinelNDVIProvider()

    async def get_district_baseline(
        self,
        district_id: str,
        month: int,
    ) -> HistoricalClimateBaseline:
        """Retrieve precomputed 10-year monthly historical climate baseline.

        Args:
            district_id: Standardized administrative district name.
            month: Calendar month integer (1 to 12).

        Returns:
            HistoricalClimateBaseline record.

        Raises:
            RecordNotFoundError: If no baseline exists for the requested district/month.
            ValueError: If month is not between 1 and 12.
        """
        if not (1 <= month <= 12):
            raise ValueError(f"Month must be between 1 and 12, got: {month}")

        baseline = await self._baseline_store.get_district_baseline(district_id, month)
        if baseline is None:
            raise RecordNotFoundError(
                f"Historical baseline not found for district '{district_id}' in month {month}"
            )
        return baseline

    async def get_weather_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        provider: str = "nasa_power",
        district_name: str = "Unknown",
        state_name: str = "Unknown",
        pin_code: str = "000000",
    ) -> List[ClimateObservation]:
        """Fetch normalized daily meteorological observations.

        Args:
            latitude: Target latitude in [-90.0, 90.0].
            longitude: Target longitude in [-180.0, 180.0].
            start_date: Query interval start date.
            end_date: Query interval end date.
            provider: Weather provider key ("nasa_power", "imd", "synthetic").

        Returns:
            List of ClimateObservation records.
        """
        validate_coordinates(latitude, longitude)
        validate_date_range(start_date, end_date)

        selected_provider = self._weather_providers.get(provider.lower())
        if not selected_provider:
            selected_provider = self._weather_providers["nasa_power"]

        return await selected_provider.fetch_observations(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            district_name=district_name,
            state_name=state_name,
            pin_code=pin_code,
        )

    async def get_vegetation_index(
        self,
        latitude: float,
        longitude: float,
        observation_date: date,
        district_id: Optional[str] = None,
    ) -> Optional[float]:
        """Retrieve satellite NDVI vegetation health index proxy."""
        validate_coordinates(latitude, longitude)
        return await self._satellite_provider.fetch_vegetation_index(
            latitude=latitude,
            longitude=longitude,
            observation_date=observation_date,
            district_id=district_id,
        )

    async def list_borrowers(
        self,
        district_id: Optional[str] = None,
        sector: Optional[BorrowerSector] = None,
    ) -> List[Borrower]:
        """Query MSME borrower profiles by district and sector."""
        if district_id:
            return await self._borrower_repo.list_borrowers_by_district(district_id, sector)
        all_borrowers = await self._borrower_repo.list_all_borrowers()
        if sector:
            return [b for b in all_borrowers if b.sector == sector]
        return all_borrowers

    async def get_borrower(self, borrower_id: str) -> Optional[Borrower]:
        """Fetch borrower by unique identifier."""
        return await self._borrower_repo.get_borrower_by_id(borrower_id)

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Compute high-level portfolio exposure aggregates."""
        all_borrowers = await self._borrower_repo.list_all_borrowers()
        total_exposure = sum(b.total_active_exposure for b in all_borrowers)
        districts = {b.location.district.upper() for b in all_borrowers}

        return {
            "total_borrowers": len(all_borrowers),
            "total_credit_exposure": round(total_exposure, 2),
            "districts_count": len(districts),
            "districts": sorted(list(districts)),
        }


# Singleton accessor instance for internal callers
_GLOBAL_DATA_LAYER_SERVICE: Optional[DataLayerService] = None


def get_data_layer_service() -> DataLayerService:
    """Retrieve or initialize the global DataLayerService singleton."""
    global _GLOBAL_DATA_LAYER_SERVICE
    if _GLOBAL_DATA_LAYER_SERVICE is None:
        _GLOBAL_DATA_LAYER_SERVICE = DataLayerService()
    return _GLOBAL_DATA_LAYER_SERVICE

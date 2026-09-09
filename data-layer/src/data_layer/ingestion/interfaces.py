"""Abstract interfaces for external weather and satellite data ingestion."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from climateshield_shared.schemas.climate import ClimateObservation, DataSourceType


class WeatherIngestionService(ABC):
    """Protocol for weather observation data ingestors (e.g. NASA POWER, IMD)."""

    @abstractmethod
    async def fetch_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        source: DataSourceType = DataSourceType.NASA_POWER,
    ) -> List[ClimateObservation]:
        """Fetch historical or daily weather telemetry observations.

        Args:
            latitude: Target latitude in decimal degrees.
            longitude: Target longitude in decimal degrees.
            start_date: Starting observation date.
            end_date: Ending observation date.
            source: Source telemetry provider.

        Returns:
            List of standardized ClimateObservation records.
        """
        pass


class SatelliteIngestionService(ABC):
    """Protocol for satellite vegetation and remote sensing proxies."""

    @abstractmethod
    async def fetch_ndvi_index(
        self,
        district_id: str,
        observation_date: date,
    ) -> Optional[float]:
        """Fetch remote sensing NDVI vegetation index proxy for a given district.

        Args:
            district_id: Standardized administrative district identifier.
            observation_date: Reference calendar date.

        Returns:
            Computed NDVI float in range [-1.0, 1.0], or None if cloud-obscured.
        """
        pass

"""Abstract repository interfaces for climate baselines and borrower portfolio seed data."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from climateshield_shared.schemas.borrower import Borrower, BorrowerSector


class HistoricalClimateBaseline(BaseModel):
    """Statistical historical baseline distributions for a geographic cluster."""
    district_id: str = Field(..., description="Target district identifier")
    month_of_year: int = Field(..., ge=1, le=12, description="Calendar month index")
    avg_rainfall_mm: float = Field(..., ge=0.0, description="10-year mean monthly rainfall")
    rainfall_std_dev_mm: float = Field(..., ge=0.0, description="Standard deviation of monthly rainfall")
    rainfall_95th_percentile_mm: float = Field(..., ge=0.0, description="Extreme precipitation 95th percentile")
    avg_max_temp_celsius: float = Field(..., description="Historical average max temperature")
    avg_ndvi_vegetation_index: float = Field(..., ge=-1.0, le=1.0, description="Average healthy seasonal NDVI")


class BaselineStore(ABC):
    """Protocol for accessing precomputed historical climate baselines."""

    @abstractmethod
    async def get_district_baseline(
        self,
        district_id: str,
        month: int,
    ) -> Optional[HistoricalClimateBaseline]:
        """Retrieve historical statistical baseline for anomaly detection.

        Args:
            district_id: Administrative district identifier.
            month: Calendar month (1-12).

        Returns:
            HistoricalClimateBaseline or None if uninitialized.
        """
        pass


class BorrowerRepository(ABC):
    """Protocol for querying MSME borrower loan portfolio profiles."""

    @abstractmethod
    async def list_borrowers_by_district(
        self,
        district_id: str,
        sector: Optional[BorrowerSector] = None,
    ) -> List[Borrower]:
        """Fetch active borrowers in a specific district, optionally filtered by sector.

        Args:
            district_id: Target administrative district.
            sector: Optional MSME enterprise sector filter.

        Returns:
            List of Borrower profile models.
        """
        pass

    @abstractmethod
    async def get_borrower_by_id(
        self,
        borrower_id: str,
    ) -> Optional[Borrower]:
        """Fetch single borrower portfolio profile by unique ID.

        Args:
            borrower_id: Unique borrower identifier.

        Returns:
            Borrower model or None if not found.
        """
        pass

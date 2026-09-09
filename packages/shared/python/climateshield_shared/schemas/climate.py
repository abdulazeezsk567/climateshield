"""Climate telemetry and environmental observation schemas.

Standardized schemas for weather, precipitation anomalies, and satellite
vegetation indices ingested from NASA POWER, IMD, or Sentinel-2 proxies.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field
from climateshield_shared.schemas.borrower import GeoLocation


class DataSourceType(str, Enum):
    """Source provider for ingested environmental telemetry."""
    NASA_POWER = "NASA_POWER"
    IMD_GRIDDED = "IMD_GRIDDED"
    SENTINEL_NDVI = "SENTINEL_NDVI"
    SYNTHETIC_SIMULATOR = "SYNTHETIC_SIMULATOR"


class ClimateObservation(BaseModel):
    """Point-in-time environmental observation data packet."""
    timestamp: datetime = Field(..., description="Timestamp of observation in UTC")
    location: GeoLocation = Field(..., description="Geographical location of measurement")
    source: DataSourceType = Field(..., description="Telemetry source provider")
    precipitation_mm: float = Field(..., ge=0.0, description="Precipitation depth in millimeters")
    temperature_celsius: float = Field(..., description="Ambient temperature in degrees Celsius")
    relative_humidity_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity percentage")
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Wind speed in kilometers per hour")
    ndvi_vegetation_index: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index")


class ClimateEvent(BaseModel):
    """Processed climate event with anomaly deviations against historical baselines."""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event detection timestamp")
    district: str = Field(..., description="Target administrative district")
    state: str = Field(..., description="Target state")
    source: DataSourceType = Field(..., description="Data provider or simulation engine")
    precipitation_anomaly_pct: float = Field(..., description="Percentage deviation from historical seasonal baseline")
    consecutive_dry_days: int = Field(default=0, ge=0, description="Consecutive dry days observed")
    consecutive_excess_rain_days: int = Field(default=0, ge=0, description="Consecutive severe rainfall days observed")
    temperature_anomaly_celsius: float = Field(default=0.0, description="Temperature deviation from historical baseline")
    ndvi_anomaly_delta: Optional[float] = Field(None, description="NDVI delta relative to historical 5-year average")
    raw_telemetry: Dict[str, float] = Field(default_factory=dict, description="Raw ingestion metrics payload")

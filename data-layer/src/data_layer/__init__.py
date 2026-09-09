"""ClimateShield Data Layer Public Interface.

Exposes the primary DataLayerService facade and domain repositories for
external layer consumption.
"""

from data_layer.service import DataLayerService, get_data_layer_service
from data_layer.exceptions import (
    DataLayerError,
    InvalidCoordinateError,
    InvalidDateRangeError,
    UpstreamAPIError,
    UpstreamMalformedResponseError,
    RecordNotFoundError,
)
from data_layer.baselines.interfaces import (
    BaselineStore,
    BorrowerRepository,
    HistoricalClimateBaseline,
)
from data_layer.ingestion.weather import (
    WeatherProvider,
    NASAPowerWeatherProvider,
    IMDWeatherProvider,
    SyntheticWeatherProvider,
)
from data_layer.ingestion.satellite import (
    SatelliteProvider,
    SentinelNDVIProvider,
)

__all__ = [
    "DataLayerService",
    "get_data_layer_service",
    "DataLayerError",
    "InvalidCoordinateError",
    "InvalidDateRangeError",
    "UpstreamAPIError",
    "UpstreamMalformedResponseError",
    "RecordNotFoundError",
    "BaselineStore",
    "BorrowerRepository",
    "HistoricalClimateBaseline",
    "WeatherProvider",
    "NASAPowerWeatherProvider",
    "IMDWeatherProvider",
    "SyntheticWeatherProvider",
    "SatelliteProvider",
    "SentinelNDVIProvider",
]

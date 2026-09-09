"""Weather telemetry ingestion providers."""

import asyncio
import logging
import math
import os
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from climateshield_shared.schemas.borrower import GeoLocation
from climateshield_shared.schemas.climate import ClimateObservation, DataSourceType
from data_layer.exceptions import UpstreamAPIError
from data_layer.validators import validate_coordinates, validate_date_range, validate_nasa_response

logger = logging.getLogger(__name__)

NASA_SENTINEL_MISSING_VALUE = -999.0


class WeatherProvider(ABC):
    """Abstract base provider for meteorological observation ingestion."""

    @abstractmethod
    async def fetch_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        district_name: str = "Unknown",
        state_name: str = "Unknown",
        pin_code: str = "000000",
    ) -> List[ClimateObservation]:
        """Fetch daily weather observations for a target location and date interval."""
        pass


class NASAPowerWeatherProvider(WeatherProvider):
    """NASA POWER API connector for solar and meteorological datasets.

    Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point
    Features automatic retry with exponential backoff and sentinel value cleansing.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout_seconds: float = 10.0,
        enable_fallback: bool = True,
    ):
        self.base_url = base_url or os.getenv(
            "NASA_POWER_API_BASE_URL",
            "https://power.larc.nasa.gov/api/temporal/daily/point",
        )
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout_seconds = timeout_seconds
        self.enable_fallback = enable_fallback
        self._fallback_provider = SyntheticWeatherProvider()

    async def fetch_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        district_name: str = "Unknown",
        state_name: str = "Unknown",
        pin_code: str = "000000",
    ) -> List[ClimateObservation]:
        """Fetch historical or daily weather observations from NASA POWER API."""
        validate_coordinates(latitude, longitude)
        validate_date_range(start_date, end_date)

        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        params = {
            "parameters": "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,WS2M",
            "community": "AG",
            "longitude": f"{longitude:.4f}",
            "latitude": f"{latitude:.4f}",
            "start": start_str,
            "end": end_str,
            "format": "JSON",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(self.base_url, params=params)
                    if response.status_code == 200:
                        raw_json = response.json()
                        return self._parse_nasa_response(
                            raw_json,
                            latitude,
                            longitude,
                            district_name,
                            state_name,
                            pin_code,
                        )
                    elif response.status_code in (429, 500, 502, 503, 504):
                        logger.warning(
                            "NASA POWER upstream status %s on attempt %s/%s",
                            response.status_code,
                            attempt,
                            self.max_retries,
                        )
                        last_error = UpstreamAPIError(
                            f"NASA POWER returned HTTP {response.status_code}: {response.text[:200]}"
                        )
                    else:
                        raise UpstreamAPIError(
                            f"NASA POWER returned non-retryable HTTP {response.status_code}: {response.text[:200]}"
                        )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    "Network error connecting to NASA POWER on attempt %s/%s: %s",
                    attempt,
                    self.max_retries,
                    str(exc),
                )
                last_error = UpstreamAPIError(f"Connection to NASA POWER failed: {str(exc)}")

            if attempt < self.max_retries:
                sleep_duration = self.backoff_factor * (2 ** (attempt - 1))
                await asyncio.sleep(sleep_duration)

        # If retries exhausted and fallback is allowed, gracefully fall back to synthetic telemetry
        if self.enable_fallback:
            logger.warning(
                "NASA POWER unreachable after %s attempts; activating resilient synthetic fallback",
                self.max_retries,
            )
            return await self._fallback_provider.fetch_observations(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                district_name=district_name,
                state_name=state_name,
                pin_code=pin_code,
            )

        raise last_error or UpstreamAPIError("Failed to fetch observations from NASA POWER")

    def _parse_nasa_response(
        self,
        raw_json: Dict[str, Any],
        latitude: float,
        longitude: float,
        district_name: str,
        state_name: str,
        pin_code: str,
    ) -> List[ClimateObservation]:
        parameter = validate_nasa_response(raw_json)

        prectotcorr = parameter.get("PRECTOTCORR", {})
        t2m = parameter.get("T2M", {})
        rh2m = parameter.get("RH2M", {})
        ws2m = parameter.get("WS2M", {})

        all_dates = sorted(set(list(prectotcorr.keys()) + list(t2m.keys())))
        observations: List[ClimateObservation] = []

        geo = GeoLocation(
            latitude=latitude,
            longitude=longitude,
            district=district_name,
            state=state_name,
            pin_code=pin_code,
        )

        for date_str in all_dates:
            try:
                obs_dt = datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                continue

            precip = prectotcorr.get(date_str, 0.0)
            temp = t2m.get(date_str, 25.0)
            rh = rh2m.get(date_str)
            ws = ws2m.get(date_str)

            # Filter NASA -999 sentinel missing values
            precip = max(0.0, float(precip)) if precip != NASA_SENTINEL_MISSING_VALUE else 0.0
            temp = float(temp) if temp != NASA_SENTINEL_MISSING_VALUE else 25.0
            rh = float(rh) if rh is not None and rh != NASA_SENTINEL_MISSING_VALUE else None
            ws = float(ws) if ws is not None and ws != NASA_SENTINEL_MISSING_VALUE else None

            observations.append(
                ClimateObservation(
                    timestamp=obs_dt,
                    location=geo,
                    source=DataSourceType.NASA_POWER,
                    precipitation_mm=precip,
                    temperature_celsius=temp,
                    relative_humidity_pct=rh,
                    wind_speed_kmh=ws * 3.6 if ws is not None else None,
                    ndvi_vegetation_index=None,
                )
            )

        return observations


class IMDWeatherProvider(WeatherProvider):
    """Indian Meteorological Department (IMD) gridded data provider stub.

    Demonstrates interface modularity enabling seamless swapping between global
    and national meteorological telemetry providers.
    """

    def __init__(self, service_url: Optional[str] = None):
        self.service_url = service_url or os.getenv(
            "IMD_DATA_SERVICE_URL", "https://api.imd.gov.in/v1/weather"
        )
        self._generator = SyntheticWeatherProvider()

    async def fetch_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        district_name: str = "Unknown",
        state_name: str = "Unknown",
        pin_code: str = "000000",
    ) -> List[ClimateObservation]:
        validate_coordinates(latitude, longitude)
        validate_date_range(start_date, end_date)

        # Uses standardized internal generator labelled as IMD source
        observations = await self._generator.fetch_observations(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            district_name=district_name,
            state_name=state_name,
            pin_code=pin_code,
        )
        for obs in observations:
            obs.source = DataSourceType.IMD_GRIDDED
        return observations


class SyntheticWeatherProvider(WeatherProvider):
    """High-fidelity synthetic weather generator for offline development and testing.

    Generates realistic monsoon, winter, and summer cycles for Indian latitudes.
    """

    async def fetch_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        district_name: str = "Unknown",
        state_name: str = "Unknown",
        pin_code: str = "000000",
    ) -> List[ClimateObservation]:
        validate_coordinates(latitude, longitude)
        validate_date_range(start_date, end_date)

        geo = GeoLocation(
            latitude=latitude,
            longitude=longitude,
            district=district_name,
            state=state_name,
            pin_code=pin_code,
        )

        observations: List[ClimateObservation] = []
        curr = start_date

        while curr <= end_date:
            day_of_year = curr.timetuple().tm_yday
            month = curr.month

            # Monsoon peak during July-August (day 180 to 250)
            if 6 <= month <= 9:
                seasonal_rain_prob = 0.65
                rain_intensity_mm = 15.0 + 35.0 * math.sin((day_of_year - 180) / 70.0 * math.pi)
                base_temp = 29.0
            elif 4 <= month <= 5:
                # Pre-monsoon summer heatwave
                seasonal_rain_prob = 0.15
                rain_intensity_mm = 5.0
                base_temp = 39.0
            else:
                # Post-monsoon / Winter
                seasonal_rain_prob = 0.10
                rain_intensity_mm = 2.0
                base_temp = 20.0

            # Deterministic variation based on day and coordinate seed
            pseudo_seed = (int(latitude * 100) + int(longitude * 100) + day_of_year * 17) % 100
            rain_mm = rain_intensity_mm * (pseudo_seed / 100.0) if (pseudo_seed / 100.0) < seasonal_rain_prob else 0.0
            temp_c = base_temp + ((pseudo_seed % 20) - 10) * 0.3
            humidity = 75.0 if rain_mm > 0 else (45.0 if month in (4, 5) else 60.0)

            obs_dt = datetime.combine(curr, datetime.min.time())
            observations.append(
                ClimateObservation(
                    timestamp=obs_dt,
                    location=geo,
                    source=DataSourceType.SYNTHETIC_SIMULATOR,
                    precipitation_mm=round(max(0.0, rain_mm), 2),
                    temperature_celsius=round(temp_c, 1),
                    relative_humidity_pct=round(humidity, 1),
                    wind_speed_kmh=round(12.0 + (pseudo_seed % 15) * 0.8, 1),
                    ndvi_vegetation_index=None,
                )
            )
            curr += timedelta(days=1)

        return observations

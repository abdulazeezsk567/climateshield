"""Unit tests for ClimateShield Data Layer."""

import asyncio
from datetime import date, datetime
import pytest
from climateshield_shared import BorrowerSector, DataSourceType
from data_layer.baselines.calculator import HistoricalBaselineCalculator
from data_layer.exceptions import InvalidCoordinateError, InvalidDateRangeError
from data_layer.ingestion.satellite import SentinelNDVIProvider
from data_layer.ingestion.weather import SyntheticWeatherProvider
from data_layer.service import DataLayerService, get_data_layer_service
from data_layer.validators import validate_coordinates, validate_date_range


def test_coordinate_validation():
    """Verify coordinate bounding checks."""
    validate_coordinates(26.76, 83.37)  # Valid Gorakhpur
    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(95.0, 83.37)  # Invalid latitude
    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(26.76, 195.0)  # Invalid longitude


def test_date_range_validation():
    """Verify chronological date validation."""
    validate_date_range(date(2026, 1, 1), date(2026, 1, 10))
    with pytest.raises(InvalidDateRangeError):
        validate_date_range(date(2026, 1, 10), date(2026, 1, 1))


def test_synthetic_weather_provider():
    """Verify synthetic weather generator outputs valid observations."""
    provider = SyntheticWeatherProvider()
    obs_list = asyncio.run(
        provider.fetch_observations(
            latitude=26.76,
            longitude=83.37,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            district_name="GORAKHPUR",
        )
    )
    assert len(obs_list) == 5
    assert all(obs.precipitation_mm >= 0.0 for obs in obs_list)
    assert all(obs.source == DataSourceType.SYNTHETIC_SIMULATOR for obs in obs_list)


def test_satellite_ndvi_provider():
    """Verify seasonal NDVI curve generation."""
    provider = SentinelNDVIProvider()
    ndvi_kharif = asyncio.run(
        provider.fetch_vegetation_index(26.76, 83.37, date(2026, 9, 25))
    )
    assert ndvi_kharif is not None
    assert 0.40 <= ndvi_kharif <= 0.85


def test_data_layer_service_facade():
    """Verify DataLayerService facade queries."""
    service = get_data_layer_service()

    # Query baseline
    baseline = asyncio.run(service.get_district_baseline("GORAKHPUR", 7))
    assert baseline.district_id == "GORAKHPUR"
    assert baseline.avg_rainfall_mm > 0.0

    # Query synthetic borrowers
    borrowers = asyncio.run(service.list_borrowers("GORAKHPUR"))
    assert len(borrowers) > 0
    assert all(b.location.district.upper() == "GORAKHPUR" for b in borrowers)

    # Query filtered by sector
    agri_borrowers = asyncio.run(service.list_borrowers("GORAKHPUR", BorrowerSector.AGRI_ALLIED))
    assert all(b.sector == BorrowerSector.AGRI_ALLIED for b in agri_borrowers)

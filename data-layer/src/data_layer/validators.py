"""Input validators and schema guards for Data Layer external requests."""

from datetime import date
from typing import Any, Dict
from data_layer.exceptions import (
    InvalidCoordinateError,
    InvalidDateRangeError,
    UpstreamMalformedResponseError,
)

MAX_QUERY_DAYS_LIMIT: int = 3650  # 10 years maximum single range query


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate latitude and longitude decimal values.

    Args:
        latitude: Target latitude in [-90.0, 90.0].
        longitude: Target longitude in [-180.0, 180.0].

    Raises:
        InvalidCoordinateError: If coordinates are out of bounds or non-numeric.
    """
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise InvalidCoordinateError(f"Coordinates must be numeric: lat={latitude}, lon={longitude}")

    if not (-90.0 <= latitude <= 90.0):
        raise InvalidCoordinateError(f"Latitude {latitude} out of bounds [-90.0, 90.0]")

    if not (-180.0 <= longitude <= 180.0):
        raise InvalidCoordinateError(f"Longitude {longitude} out of bounds [-180.0, 180.0]")


def validate_date_range(start_date: date, end_date: date) -> None:
    """Validate date query intervals.

    Args:
        start_date: Starting observation date.
        end_date: Ending observation date.

    Raises:
        InvalidDateRangeError: If start > end or span exceeds limit.
    """
    if start_date > end_date:
        raise InvalidDateRangeError(
            f"start_date ({start_date}) cannot be after end_date ({end_date})"
        )

    delta_days = (end_date - start_date).days
    if delta_days > MAX_QUERY_DAYS_LIMIT:
        raise InvalidDateRangeError(
            f"Date range span of {delta_days} days exceeds maximum permitted limit of {MAX_QUERY_DAYS_LIMIT} days"
        )


def validate_nasa_response(raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """Validate NASA POWER API response structure.

    Args:
        raw_json: Decoded JSON response from NASA POWER API.

    Returns:
        The validated parameter dictionary.

    Raises:
        UpstreamMalformedResponseError: If required keys or parameter blocks are missing.
    """
    if not isinstance(raw_json, dict):
        raise UpstreamMalformedResponseError("NASA POWER response must be a JSON object")

    properties = raw_json.get("properties")
    if not isinstance(properties, dict):
        raise UpstreamMalformedResponseError("Missing or invalid 'properties' block in NASA response")

    parameter = properties.get("parameter")
    if not isinstance(parameter, dict):
        raise UpstreamMalformedResponseError("Missing or invalid 'parameter' block in NASA response")

    # Verify at least precipitation and temperature parameters exist
    if "PRECTOTCORR" not in parameter and "T2M" not in parameter:
        raise UpstreamMalformedResponseError(
            "Neither 'PRECTOTCORR' nor 'T2M' found in NASA response parameters"
        )

    return parameter

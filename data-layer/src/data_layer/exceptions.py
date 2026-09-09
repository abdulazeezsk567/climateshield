"""Exception hierarchy for ClimateShield Data Layer."""


class DataLayerError(Exception):
    """Base exception for all data layer errors."""
    pass


class InvalidCoordinateError(DataLayerError):
    """Raised when geographic coordinates are outside valid bounds."""
    pass


class InvalidDateRangeError(DataLayerError):
    """Raised when query date ranges are inverted, malformed, or exceed limits."""
    pass


class UpstreamAPIError(DataLayerError):
    """Raised when a third-party meteorological or satellite API fails."""
    pass


class UpstreamMalformedResponseError(DataLayerError):
    """Raised when an upstream API returns an unexpected or corrupted payload shape."""
    pass


class RecordNotFoundError(DataLayerError):
    """Raised when a requested borrower, district, or baseline record is not found."""
    pass

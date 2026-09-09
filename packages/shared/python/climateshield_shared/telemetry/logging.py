"""Structured JSON logging and telemetry formatter for ClimateShield."""

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Any, Dict, Optional

# Patterns and key names requiring redaction to maintain borrower privacy
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(borrower_name|phone|pan|aadhaar|account_number|password|secret|token|authorization)",
    re.IGNORECASE,
)


class StructuredJsonFormatter(logging.Formatter):
    """Formats standard Python logging records into single-line JSON objects.

    Produces output directly ingestible by log aggregators (Datadog, AWS CloudWatch,
    ELK/Elasticsearch, Grafana Loki, Fluentd) with standardized timestamps,
    log severity levels, service markers, and correlation IDs.
    """

    def __init__(
        self,
        service_name: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.service_name = service_name or os.getenv("SERVICE_NAME", "climateshield")
        self.environment = environment or os.getenv("ENVIRONMENT", "development")

    def _sanitize_data(self, data: Any) -> Any:
        """Recursively redact sensitive borrower and credential information."""
        if isinstance(data, dict):
            clean: Dict[str, Any] = {}
            for k, v in data.items():
                if SENSITIVE_KEY_PATTERNS.search(str(k)):
                    clean[k] = "[REDACTED]"
                else:
                    clean[k] = self._sanitize_data(v)
            return clean
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def format(self, record: logging.LogRecord) -> str:
        """Format a LogRecord into a standardized JSON payload."""
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", self.service_name),
            "environment": self.environment,
        }

        # Attach request or correlation tracking ID if present
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_entry["correlation_id"] = record.correlation_id
        if hasattr(record, "request_id") and record.request_id:
            log_entry["request_id"] = record.request_id

        # Attach extra structured fields passed in record.__dict__
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "correlation_id", "request_id",
            "service",
        }
        extra_fields = {}
        for k, v in record.__dict__.items():
            if k not in standard_attrs and not k.startswith("_"):
                if SENSITIVE_KEY_PATTERNS.search(str(k)):
                    extra_fields[k] = "[REDACTED]"
                else:
                    extra_fields[k] = self._sanitize_data(v)
        if extra_fields:
            log_entry["context"] = extra_fields

        # Include formatted exception trace if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_entry["exception"] = record.exc_text

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configures the root logging subsystem for a given service.

    Args:
        service_name: Descriptive name of the microservice (e.g. 'climateshield-api').
        log_level: Python log level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        json_format: If True, uses StructuredJsonFormatter; otherwise uses standard text.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove pre-existing handlers to prevent duplicated output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)

    if json_format:
        handler.setFormatter(StructuredJsonFormatter(service_name=service_name))
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

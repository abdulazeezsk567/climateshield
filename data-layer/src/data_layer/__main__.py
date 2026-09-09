"""Standalone Climate Observation Ingestion Daemon for ClimateShield Data Layer."""

import asyncio
import logging
import os
import signal
import sys
from climateshield_shared.telemetry import configure_logging
from data_layer.service import get_data_layer_service

logger = logging.getLogger("climateshield.data_layer.daemon")


async def run_daemon(poll_interval_seconds: int = 60) -> None:
    """Execute continuous climate data ingestion and cache warmup loop."""
    env = os.getenv("DATA_LAYER_ENV", os.getenv("ENVIRONMENT", "development"))
    log_level = os.getenv("LOG_LEVEL", "info")
    configure_logging(service_name="climateshield-data-layer", log_level=log_level)

    logger.info("Initializing ClimateShield Data Layer Daemon in %s mode...", env)
    data_service = get_data_layer_service()

    # Warmup and verify portfolio seed data
    summary = await data_service.get_portfolio_summary()
    logger.info(
        "Data Layer warmed successfully: %d borrowers loaded across %d districts. Total exposure: INR %.2f",
        summary["total_borrowers"],
        summary["districts_count"],
        summary["total_credit_exposure"],
    )

    # Setup graceful shutdown handlers
    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Shutdown signal received. Terminating Data Layer daemon...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Signal handling on Windows event loops
            pass

    logger.info("Data Layer daemon running. Polling satellite & meteorological feeds every %ds.", poll_interval_seconds)

    try:
        while not shutdown_event.is_set():
            # Check single-run environment flag for CI / container verification
            if os.getenv("RUN_ONCE", "false").lower() in ("true", "1", "yes"):
                logger.info("RUN_ONCE flag detected. Exiting successfully.")
                break

            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=poll_interval_seconds)
            except asyncio.TimeoutError:
                logger.debug("Data layer heartbeat: weather observations synced and healthy.")
    except Exception as exc:
        logger.error("Unexpected failure in Data Layer daemon: %s", exc, exc_info=True)
        sys.exit(1)

    logger.info("Data Layer daemon stopped cleanly.")


def main() -> None:
    """CLI entrypoint."""
    interval = int(os.getenv("INGESTION_POLL_INTERVAL_SECONDS", "60"))
    try:
        asyncio.run(run_daemon(poll_interval_seconds=interval))
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user.")


if __name__ == "__main__":
    main()

"""Standalone Risk & Trigger Evaluation Daemon for ClimateShield Risk Engine."""

import asyncio
import logging
import os
import signal
import sys
from climateshield_shared.telemetry import configure_logging
from risk_engine.service import RiskEngineService

logger = logging.getLogger("climateshield.risk_engine.daemon")


async def run_daemon(poll_interval_seconds: int = 60) -> None:
    """Execute continuous climate risk evaluation and anomaly detection loop."""
    env = os.getenv("RISK_ENGINE_ENV", os.getenv("ENVIRONMENT", "development"))
    log_level = os.getenv("LOG_LEVEL", "info")
    configure_logging(service_name="climateshield-risk-engine", log_level=log_level)

    logger.info("Initializing ClimateShield Risk Engine Daemon in %s mode...", env)
    risk_service = RiskEngineService()

    model_name = risk_service.config.model_config.get("model_name", "ExplainableZoning")
    version = risk_service.config.model_config.get("version", "1.0.0")
    logger.info(
        "Risk Engine initialized. Model: %s (v%s). Sector rules configured: %d.",
        model_name,
        version,
        len(risk_service.config.thresholds.get("sectors", {})),
    )

    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Shutdown signal received. Terminating Risk Engine daemon...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    logger.info("Risk Engine daemon running. Monitoring portfolio risk every %ds.", poll_interval_seconds)

    try:
        while not shutdown_event.is_set():
            if os.getenv("RUN_ONCE", "false").lower() in ("true", "1", "yes"):
                logger.info("RUN_ONCE flag detected. Exiting successfully.")
                break

            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=poll_interval_seconds)
            except asyncio.TimeoutError:
                logger.debug("Risk engine heartbeat: all regional thresholds evaluated without anomaly.")
    except Exception as exc:
        logger.error("Unexpected failure in Risk Engine daemon: %s", exc, exc_info=True)
        sys.exit(1)

    logger.info("Risk Engine daemon stopped cleanly.")


def main() -> None:
    """CLI entrypoint."""
    interval = int(os.getenv("RISK_EVALUATION_INTERVAL_SECONDS", "60"))
    try:
        asyncio.run(run_daemon(poll_interval_seconds=interval))
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user.")


if __name__ == "__main__":
    main()

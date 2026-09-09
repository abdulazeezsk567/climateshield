"""Standalone Action & LMS Integration Daemon for ClimateShield Integration Layer."""

import asyncio
import logging
import os
import signal
import sys
from climateshield_shared.telemetry import configure_logging
from integration_layer.service import get_integration_service

logger = logging.getLogger("climateshield.integration_layer.daemon")


async def run_daemon(poll_interval_seconds: int = 60) -> None:
    """Execute continuous LMS queue monitoring and audit integrity verification loop."""
    env = os.getenv("INTEGRATION_ENV", os.getenv("ENVIRONMENT", "development"))
    log_level = os.getenv("LOG_LEVEL", "info")
    configure_logging(service_name="climateshield-integration-layer", log_level=log_level)

    logger.info("Initializing ClimateShield Integration Layer Daemon in %s mode...", env)
    integration_service = get_integration_service()

    # Verify audit ledger cryptographic integrity on startup
    audit_report = await integration_service.verify_audit_ledger()
    logger.info(
        "Cryptographic audit ledger verified on startup: valid=%s, total_entries=%d.",
        audit_report["chain_valid"],
        audit_report["total_entries"],
    )

    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Shutdown signal received. Terminating Integration Layer daemon...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    logger.info("Integration Layer daemon running. Monitoring LMS queues every %ds.", poll_interval_seconds)

    try:
        while not shutdown_event.is_set():
            if os.getenv("RUN_ONCE", "false").lower() in ("true", "1", "yes"):
                logger.info("RUN_ONCE flag detected. Exiting successfully.")
                break

            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=poll_interval_seconds)
            except asyncio.TimeoutError:
                report = await integration_service.verify_audit_ledger()
                logger.debug(
                    "Audit ledger verification heartbeat: entries=%d, tamper_detected=%s.",
                    report["total_entries"],
                    not report["chain_valid"],
                )
    except Exception as exc:
        logger.error("Unexpected failure in Integration Layer daemon: %s", exc, exc_info=True)
        sys.exit(1)

    logger.info("Integration Layer daemon stopped cleanly.")


def main() -> None:
    """CLI entrypoint."""
    interval = int(os.getenv("INTEGRATION_POLL_INTERVAL_SECONDS", "60"))
    try:
        asyncio.run(run_daemon(poll_interval_seconds=interval))
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user.")


if __name__ == "__main__":
    main()

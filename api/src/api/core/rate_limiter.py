"""Sliding-window in-memory rate limiter and security anomaly detector."""

from collections import defaultdict
from datetime import datetime, timezone
import logging
import threading
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("api.security.anomaly")


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter with anomaly tracking."""

    def __init__(self):
        self._lock = threading.Lock()
        # Mapping key -> list of request timestamps (epoch floats)
        self._request_history: Dict[str, List[float]] = defaultdict(list)
        # Mapping key -> list of failed auth attempt timestamps
        self._auth_failure_history: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int]:
        """Check if a key (IP or token) has exceeded the permitted rate limit.

        Args:
            key: Rate limiting key (e.g. client IP or user token).
            limit: Maximum requests allowed within window_seconds.
            window_seconds: Duration of the sliding window in seconds.

        Returns:
            Tuple of (is_limited: bool, retry_after_seconds: int).
        """
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds

        with self._lock:
            history = self._request_history[key]
            # Prune timestamps older than cutoff
            self._request_history[key] = [t for t in history if t > cutoff]
            current_count = len(self._request_history[key])

            if current_count >= limit:
                # Oldest timestamp within window determines retry_after
                oldest_in_window = self._request_history[key][0]
                retry_after = max(1, int(oldest_in_window + window_seconds - now))
                return True, retry_after

            # Record this request
            self._request_history[key].append(now)
            return False, 0

    def record_auth_failure(
        self,
        identifier: str,
        ip_address: str,
        threshold: int = 3,
        window_seconds: int = 300,
    ) -> None:
        """Record an authentication failure and emit anomaly alerts on repeated breaches.

        Args:
            identifier: Username or attempted account handle.
            ip_address: Origin client IP.
            threshold: Number of failures within window triggering an alert.
            window_seconds: Evaluation window (default 5 minutes).
        """
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds
        key = f"{ip_address}:{identifier}"

        with self._lock:
            history = self._auth_failure_history[key]
            self._auth_failure_history[key] = [t for t in history if t > cutoff]
            self._auth_failure_history[key].append(now)
            failure_count = len(self._auth_failure_history[key])

            if failure_count >= threshold:
                logger.warning(
                    "[SECURITY_ANOMALY] Repeated authentication failures detected: "
                    "ip=%s username='%s' failure_count=%d within %ds window. Potential brute-force attempt.",
                    ip_address,
                    identifier,
                    failure_count,
                    window_seconds,
                )

    def reset(self) -> None:
        """Clear all in-memory rate limiting and failure tracking state (useful for tests)."""
        with self._lock:
            self._request_history.clear()
            self._auth_failure_history.clear()


# Global rate limiter singleton
rate_limiter = SlidingWindowRateLimiter()

"""Thread-safe in-memory metrics registry for ClimateShield services.

Tracks operational throughput, latency distributions, HTTP error rates,
climate trigger evaluation counts, and LMS relief intervention dispatches.
Provides both standard Prometheus exposition format and JSON summaries.
"""

from collections import defaultdict
import threading
from typing import Any, Dict, Optional


class MetricsRegistry:
    """Central metrics collector supporting Prometheus and JSON exposition."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        """Reset all tracked metrics to zero (useful for testing)."""
        with getattr(self, "_lock", threading.Lock()):
            self._http_requests: Dict[str, int] = defaultdict(int)
            self._http_errors: Dict[str, int] = defaultdict(int)
            self._http_durations_sum: Dict[str, float] = defaultdict(float)
            self._http_durations_count: Dict[str, int] = defaultdict(int)
            self._triggers_evaluated: Dict[str, int] = defaultdict(int)
            self._triggers_fired: Dict[str, int] = defaultdict(int)
            self._interventions_dispatched: Dict[str, int] = defaultdict(int)

    def increment_http_requests(self, method: str, endpoint: str, status_code: int) -> None:
        """Record an incoming HTTP request execution."""
        key = f"{method.upper()}|{endpoint}|{status_code}"
        with self._lock:
            self._http_requests[key] += 1

    def observe_http_duration(self, endpoint: str, duration_seconds: float) -> None:
        """Record the latency duration in seconds for an endpoint."""
        with self._lock:
            self._http_durations_sum[endpoint] += duration_seconds
            self._http_durations_count[endpoint] += 1

    def increment_http_errors(self, status_code: int, error_code: str) -> None:
        """Record an HTTP error occurrence (4xx or 5xx)."""
        key = f"{status_code}|{error_code}"
        with self._lock:
            self._http_errors[key] += 1

    def increment_triggers_evaluated(self, hazard_type: str, district: str) -> None:
        """Record climate trigger rule assessment."""
        key = f"{hazard_type.upper()}|{district.upper()}"
        with self._lock:
            self._triggers_evaluated[key] += 1

    def increment_triggers_fired(self, hazard_type: str, district: str) -> None:
        """Record a successful climate anomaly trigger activation."""
        key = f"{hazard_type.upper()}|{district.upper()}"
        with self._lock:
            self._triggers_fired[key] += 1

    def increment_interventions_dispatched(self, relief_type: str) -> None:
        """Record an automated LMS loan-support intervention action."""
        key = relief_type.upper()
        with self._lock:
            self._interventions_dispatched[key] += 1

    def to_dict(self) -> Dict[str, Any]:
        """Produce a structured dictionary summary of current system metrics."""
        with self._lock:
            total_requests = sum(self._http_requests.values())
            total_errors = sum(self._http_errors.values())
            error_rate_pct = round((total_errors / total_requests * 100.0), 2) if total_requests > 0 else 0.0

            requests_by_status: Dict[str, int] = defaultdict(int)
            for k, count in self._http_requests.items():
                parts = k.split("|")
                if len(parts) == 3:
                    requests_by_status[parts[2]] += count

            endpoint_latencies: Dict[str, Dict[str, float]] = {}
            for ep, count in self._http_durations_count.items():
                total_duration = self._http_durations_sum.get(ep, 0.0)
                avg_sec = round(total_duration / count, 4) if count > 0 else 0.0
                endpoint_latencies[ep] = {
                    "count": count,
                    "avg_seconds": avg_sec,
                    "total_seconds": round(total_duration, 4),
                }

            return {
                "http": {
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "error_rate_percent": error_rate_pct,
                    "status_breakdown": dict(requests_by_status),
                    "latencies": endpoint_latencies,
                },
                "triggers": {
                    "total_evaluated": sum(self._triggers_evaluated.values()),
                    "total_fired": sum(self._triggers_fired.values()),
                    "by_hazard": {
                        k: count for k, count in self._triggers_fired.items()
                    },
                },
                "interventions": {
                    "total_dispatched": sum(self._interventions_dispatched.values()),
                    "by_relief_type": dict(self._interventions_dispatched),
                },
            }

    def to_prometheus_format(self) -> str:
        """Render metrics into standard Prometheus exposition format (v0.0.4)."""
        lines = []

        with self._lock:
            # 1. HTTP Requests Total
            lines.append("# HELP climateshield_http_requests_total Total count of HTTP requests handled.")
            lines.append("# TYPE climateshield_http_requests_total counter")
            if not self._http_requests:
                lines.append('climateshield_http_requests_total{method="GET",endpoint="/health",status="200"} 0')
            for key, count in sorted(self._http_requests.items()):
                method, endpoint, status = key.split("|")
                lines.append(f'climateshield_http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}')

            # 2. HTTP Errors Total
            lines.append("# HELP climateshield_http_errors_total Total count of HTTP errors (4xx and 5xx).")
            lines.append("# TYPE climateshield_http_errors_total counter")
            for key, count in sorted(self._http_errors.items()):
                status, err_code = key.split("|")
                lines.append(f'climateshield_http_errors_total{{status="{status}",error_code="{err_code}"}} {count}')

            # 3. HTTP Request Latency Summary
            lines.append("# HELP climateshield_http_request_duration_seconds Latency summary of HTTP requests.")
            lines.append("# TYPE climateshield_http_request_duration_seconds summary")
            for endpoint, count in sorted(self._http_durations_count.items()):
                sum_sec = self._http_durations_sum.get(endpoint, 0.0)
                lines.append(f'climateshield_http_request_duration_seconds_sum{{endpoint="{endpoint}"}} {sum_sec:.6f}')
                lines.append(f'climateshield_http_request_duration_seconds_count{{endpoint="{endpoint}"}} {count}')

            # 4. Triggers Evaluated Total
            lines.append("# HELP climateshield_triggers_evaluated_total Total climate anomalies evaluated.")
            lines.append("# TYPE climateshield_triggers_evaluated_total counter")
            for key, count in sorted(self._triggers_evaluated.items()):
                hazard, district = key.split("|")
                lines.append(f'climateshield_triggers_evaluated_total{{hazard="{hazard}",district="{district}"}} {count}')

            # 5. Triggers Fired Total
            lines.append("# HELP climateshield_triggers_fired_total Total climate anomaly triggers activated.")
            lines.append("# TYPE climateshield_triggers_fired_total counter")
            for key, count in sorted(self._triggers_fired.items()):
                hazard, district = key.split("|")
                lines.append(f'climateshield_triggers_fired_total{{hazard="{hazard}",district="{district}"}} {count}')

            # 6. Interventions Dispatched Total
            lines.append("# HELP climateshield_interventions_dispatched_total Total LMS interventions dispatched.")
            lines.append("# TYPE climateshield_interventions_dispatched_total counter")
            for relief_type, count in sorted(self._interventions_dispatched.items()):
                lines.append(f'climateshield_interventions_dispatched_total{{relief_type="{relief_type}"}} {count}')

        lines.append("")
        return "\n".join(lines)


# Singleton instance
_GLOBAL_METRICS_REGISTRY: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """Obtain or instantiate the global MetricsRegistry singleton."""
    global _GLOBAL_METRICS_REGISTRY
    if _GLOBAL_METRICS_REGISTRY is None:
        _GLOBAL_METRICS_REGISTRY = MetricsRegistry()
    return _GLOBAL_METRICS_REGISTRY

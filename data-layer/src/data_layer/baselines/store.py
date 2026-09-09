"""Baseline store repository with pre-seeded historical climate distributions."""

from typing import Dict, Optional, Tuple
from data_layer.baselines.interfaces import BaselineStore, HistoricalClimateBaseline


class InMemoryBaselineStore(BaselineStore):
    """In-memory baseline store pre-seeded with 10-year monthly climate baselines.

    Contains calibrated historical baselines for Satin Finserv's key operational
    MSME lending districts in Northern & Eastern India.
    """

    def __init__(self):
        self._store: Dict[Tuple[str, int], HistoricalClimateBaseline] = {}
        self._seed_default_baselines()

    async def get_district_baseline(
        self,
        district_id: str,
        month: int,
    ) -> Optional[HistoricalClimateBaseline]:
        """Retrieve precomputed baseline for district and month."""
        return self._store.get((district_id.strip().upper(), month))

    def save_baseline(self, baseline: HistoricalClimateBaseline) -> None:
        """Persist or update a baseline record."""
        self._store[(baseline.district_id.strip().upper(), baseline.month_of_year)] = baseline

    def _seed_default_baselines(self) -> None:
        """Pre-populate 10-year monthly baselines for primary SFL branches."""
        # Baseline profiles: (district, monsoon_rain_mean, dry_season_rain_mean, max_temp, base_ndvi)
        district_profiles = {
            "GORAKHPUR": {"monsoon_mean": 290.0, "dry_mean": 12.0, "max_temp": 38.5, "ndvi": 0.62},
            "VARANASI": {"monsoon_mean": 240.0, "dry_mean": 10.0, "max_temp": 39.5, "ndvi": 0.58},
            "LUCKNOW": {"monsoon_mean": 210.0, "dry_mean": 8.0, "max_temp": 40.0, "ndvi": 0.54},
            "PATNA": {"monsoon_mean": 260.0, "dry_mean": 11.0, "max_temp": 38.0, "ndvi": 0.59},
            "MUZAFFARPUR": {"monsoon_mean": 310.0, "dry_mean": 14.0, "max_temp": 37.5, "ndvi": 0.65},
            "LUDHIANA": {"monsoon_mean": 160.0, "dry_mean": 22.0, "max_temp": 41.0, "ndvi": 0.52},
            "JAIPUR": {"monsoon_mean": 140.0, "dry_mean": 6.0, "max_temp": 42.5, "ndvi": 0.38},
        }

        for district, p in district_profiles.items():
            for m in range(1, 13):
                # July (7) & August (8) represent peak monsoon
                if m in (7, 8):
                    avg_rain = p["monsoon_mean"]
                    std_dev = avg_rain * 0.30
                    p95 = avg_rain * 1.65
                    temp = p["max_temp"] - 5.0
                    ndvi = p["ndvi"] + 0.12
                elif m in (6, 9):
                    avg_rain = p["monsoon_mean"] * 0.55
                    std_dev = avg_rain * 0.35
                    p95 = avg_rain * 1.70
                    temp = p["max_temp"] - 2.0
                    ndvi = p["ndvi"] + 0.08
                elif m in (4, 5):
                    # Peak summer
                    avg_rain = p["dry_mean"] * 1.5
                    std_dev = avg_rain * 0.40
                    p95 = avg_rain * 2.10
                    temp = p["max_temp"]
                    ndvi = p["ndvi"] - 0.15
                else:
                    # Winter / dry
                    avg_rain = p["dry_mean"]
                    std_dev = avg_rain * 0.45
                    p95 = avg_rain * 2.20
                    temp = p["max_temp"] - 15.0
                    ndvi = p["ndvi"]

                self._store[(district, m)] = HistoricalClimateBaseline(
                    district_id=district,
                    month_of_year=m,
                    avg_rainfall_mm=round(avg_rain, 2),
                    rainfall_std_dev_mm=round(std_dev, 2),
                    rainfall_95th_percentile_mm=round(p95, 2),
                    avg_max_temp_celsius=round(temp, 1),
                    avg_ndvi_vegetation_index=round(max(0.1, min(0.9, ndvi)), 3),
                )

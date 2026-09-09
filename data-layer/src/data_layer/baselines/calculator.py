"""Statistical historical baseline calculation engine."""

import math
from collections import defaultdict
from typing import Dict, List
from climateshield_shared.schemas.climate import ClimateObservation
from data_layer.baselines.interfaces import HistoricalClimateBaseline


class HistoricalBaselineCalculator:
    """Computes multi-year statistical distribution baselines from observation series."""

    @staticmethod
    def calculate_monthly_baselines(
        district_id: str,
        observations: List[ClimateObservation],
    ) -> Dict[int, HistoricalClimateBaseline]:
        """Compute monthly mean, standard deviation, and 95th percentile baselines.

        Args:
            district_id: Administrative district identifier.
            observations: Historical timeseries of ClimateObservation records.

        Returns:
            Dictionary mapping month_of_year (1-12) to HistoricalClimateBaseline.
        """
        monthly_precip: Dict[int, List[float]] = defaultdict(list)
        monthly_temp: Dict[int, List[float]] = defaultdict(list)
        monthly_ndvi: Dict[int, List[float]] = defaultdict(list)

        for obs in observations:
            m = obs.timestamp.month
            monthly_precip[m].append(obs.precipitation_mm)
            monthly_temp[m].append(obs.temperature_celsius)
            if obs.ndvi_vegetation_index is not None:
                monthly_ndvi[m].append(obs.ndvi_vegetation_index)

        baselines: Dict[int, HistoricalClimateBaseline] = {}

        for m in range(1, 13):
            precip_vals = monthly_precip.get(m, [0.0])
            temp_vals = monthly_temp.get(m, [25.0])
            ndvi_vals = monthly_ndvi.get(m, [0.35])

            # Mean
            mean_rain = sum(precip_vals) / max(1, len(precip_vals))
            mean_temp = sum(temp_vals) / max(1, len(temp_vals))
            mean_ndvi = sum(ndvi_vals) / max(1, len(ndvi_vals))

            # Standard deviation
            variance = sum((x - mean_rain) ** 2 for x in precip_vals) / max(1, len(precip_vals))
            std_dev_rain = math.sqrt(variance)

            # 95th percentile
            sorted_precip = sorted(precip_vals)
            p95_idx = int(0.95 * (len(sorted_precip) - 1))
            p95_rain = sorted_precip[p95_idx]

            baselines[m] = HistoricalClimateBaseline(
                district_id=district_id.upper(),
                month_of_year=m,
                avg_rainfall_mm=round(mean_rain, 2),
                rainfall_std_dev_mm=round(std_dev_rain, 2),
                rainfall_95th_percentile_mm=round(p95_rain, 2),
                avg_max_temp_celsius=round(mean_temp, 1),
                avg_ndvi_vegetation_index=round(mean_ndvi, 3),
            )

        return baselines

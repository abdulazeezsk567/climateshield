"""Configuration loader for Risk Engine thresholds and ML model parameters."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path(__file__).resolve().parent
DEFAULT_THRESHOLDS_PATH = CONFIG_DIR / "thresholds.json"
DEFAULT_MODEL_CONFIG_PATH = CONFIG_DIR / "model_config.json"


class RiskEngineConfig:
    """Manages externalized threshold settings and model calibration parameters."""

    def __init__(
        self,
        thresholds_path: Optional[Path] = None,
        model_config_path: Optional[Path] = None,
    ):
        self.thresholds_path = thresholds_path or DEFAULT_THRESHOLDS_PATH
        self.model_config_path = model_config_path or DEFAULT_MODEL_CONFIG_PATH
        self._thresholds_cache: Dict[str, Any] = {}
        self._model_config_cache: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload configuration files from disk.

        Enables hot-recalibration of risk thresholds without restarting the service.
        """
        with open(self.thresholds_path, "r", encoding="utf-8") as f:
            self._thresholds_cache = json.load(f)

        with open(self.model_config_path, "r", encoding="utf-8") as f:
            self._model_config_cache = json.load(f)

    @property
    def thresholds(self) -> Dict[str, Any]:
        """Sector-specific trigger threshold rules."""
        return self._thresholds_cache

    @property
    def model_config(self) -> Dict[str, Any]:
        """ML feature weights and explainability parameters."""
        return self._model_config_cache

    def get_sector_threshold(self, sector_key: str) -> Dict[str, Any]:
        """Get threshold parameters for a specific MSME business sector."""
        sectors = self._thresholds_cache.get("sectors", {})
        if sector_key in sectors:
            return sectors[sector_key]
        # Fallback to default / retail sector if sector unknown
        return sectors.get("RETAIL_MICRO_ENTERPRISE", {
            "rainfall_deficit_pct": -50.0,
            "excess_rainfall_percentile": 95.0,
            "heatwave_consecutive_days": 4,
            "ndvi_vegetation_stress_pct": -40.0,
            "priority_weight": 0.5,
        })

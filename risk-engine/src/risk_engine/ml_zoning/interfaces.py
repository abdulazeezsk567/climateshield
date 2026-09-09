"""Abstract interfaces for machine learning microclimate zoning."""

from abc import ABC, abstractmethod
from typing import Dict, List
from pydantic import BaseModel, Field
from climateshield_shared.constants import RiskTier


class ZoningPrediction(BaseModel):
    """Output prediction for an ML-classified microclimate vulnerability zone."""
    zone_cluster_id: str = Field(..., description="Unique cluster identifier")
    risk_tier: RiskTier = Field(..., description="Predicted vulnerability category")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence")
    feature_importances: Dict[str, float] = Field(default_factory=dict, description="Key influencing feature weights")


class MLZoningClassifier(ABC):
    """Protocol for machine learning climate zoning classifiers."""

    @abstractmethod
    def predict_zone_vulnerability(
        self,
        features: Dict[str, float],
    ) -> ZoningPrediction:
        """Classify microclimate hazard and environmental features into a vulnerability zone.

        Args:
            features: Dictionary of normalized environmental, topographical, and crop features.

        Returns:
            ZoningPrediction record.
        """
        pass

    @abstractmethod
    def batch_predict(
        self,
        feature_batch: List[Dict[str, float]],
    ) -> List[ZoningPrediction]:
        """Perform batch classification over multiple geographical nodes.

        Args:
            feature_batch: List of feature dictionaries.

        Returns:
            List of ZoningPrediction records.
        """
        pass

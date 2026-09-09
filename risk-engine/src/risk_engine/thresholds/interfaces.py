"""Abstract protocols for threshold evaluation and risk scoring."""

from abc import ABC, abstractmethod
from typing import List, Optional
from climateshield_shared.schemas.borrower import Borrower
from climateshield_shared.schemas.climate import ClimateEvent
from climateshield_shared.schemas.trigger import RiskAssessment, TriggerEvent


class ThresholdEngine(ABC):
    """Protocol for rule-based parametric threshold evaluation."""

    @abstractmethod
    def evaluate_triggers(
        self,
        climate_event: ClimateEvent,
        affected_borrowers: List[Borrower],
    ) -> Optional[TriggerEvent]:
        """Evaluate whether a climate event breaches policy thresholds for borrowers.

        Args:
            climate_event: Ingested climate anomaly event record.
            affected_borrowers: List of active borrowers in the impacted region.

        Returns:
            TriggerEvent if threshold breached, otherwise None.
        """
        pass


class RiskCalculator(ABC):
    """Protocol for assessing continuous composite risk indices."""

    @abstractmethod
    def calculate_borrower_risk(
        self,
        borrower: Borrower,
        climate_event: ClimateEvent,
    ) -> RiskAssessment:
        """Calculate multi-hazard composite risk index for an individual borrower.

        Args:
            borrower: MSME borrower profile with loan exposure.
            climate_event: Climate anomaly context.

        Returns:
            Comprehensive RiskAssessment record.
        """
        pass

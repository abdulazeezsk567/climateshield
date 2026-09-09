"""Borrower and Loan Portfolio data models.

Defines schemas for MSME borrower seed profiles and loan metadata, adhering
to data minimization and privacy standards.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class BorrowerSector(str, Enum):
    """MSME business sector classification."""
    AGRI_ALLIED = "AGRI_ALLIED"
    DAIRY_LIVESTOCK = "DAIRY_LIVESTOCK"
    HANDLOOMS_TEXTILES = "HANDLOOMS_TEXTILES"
    FOOD_PROCESSING = "FOOD_PROCESSING"
    RETAIL_MICRO_ENTERPRISE = "RETAIL_MICRO_ENTERPRISE"
    SERVICES_LIGHT_MANUFACTURING = "SERVICES_LIGHT_MANUFACTURING"


class GeoLocation(BaseModel):
    """Geographical coordinate and administrative boundary model."""
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    district: str = Field(..., description="District administrative name")
    state: str = Field(..., description="State administrative name")
    pin_code: str = Field(..., description="Postal code (PIN)")


class LoanSummary(BaseModel):
    """High-level summary of an active MSME loan contract."""
    loan_id: str = Field(..., description="Unique LMS loan account identifier")
    disbursed_principal: float = Field(..., gt=0, description="Original disbursed loan principal")
    current_outstanding_balance: float = Field(..., ge=0, description="Current remaining balance")
    monthly_emi_amount: float = Field(..., gt=0, description="Standard monthly EMI amount")
    tenure_months_remaining: int = Field(..., ge=0, description="Remaining loan tenure in months")
    currency: str = Field(default="INR", description="Three-letter ISO currency code")


class Borrower(BaseModel):
    """Standardized representation of an MSME borrower portfolio entry."""
    borrower_id: str = Field(..., description="Anonymized borrower unique identifier")
    anonymized_alias: str = Field(..., description="De-identified stakeholder display alias")
    sector: BorrowerSector = Field(..., description="MSME enterprise industry classification")
    location: GeoLocation = Field(..., description="Borrower primary operational geolocation")
    active_loans: List[LoanSummary] = Field(default_factory=list, description="Associated active loan accounts")
    total_active_exposure: float = Field(default=0.0, ge=0, description="Aggregated active credit exposure")
    contact_token: Optional[str] = Field(None, description="Hashed token for borrower communication routing")

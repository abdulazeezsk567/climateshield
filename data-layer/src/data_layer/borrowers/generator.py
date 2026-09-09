"""Synthetic MSME borrower and loan seed dataset generator.

NOTICE: This generator produces strictly synthetic demo data for testing and
demonstration purposes. It does not contain any real borrower PII or actual NBFC
credit records.
"""

from typing import List
from climateshield_shared.schemas.borrower import (
    Borrower,
    BorrowerSector,
    GeoLocation,
    LoanSummary,
)

# Clearly labelled placeholder parameters for synthetic loans:
DEFAULT_SYNTHETIC_INTEREST_RATE_PLACEHOLDER: float = 0.18  # 18% annual placeholder
DEFAULT_CURRENCY: str = "INR"

# Representative geographic coordinates for SFL branch centers:
DISTRICT_COORDINATES = {
    "GORAKHPUR": {"lat": 26.7606, "lon": 83.3732, "state": "Uttar Pradesh", "pin": "273001"},
    "VARANASI": {"lat": 25.3176, "lon": 82.9739, "state": "Uttar Pradesh", "pin": "221001"},
    "LUCKNOW": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "pin": "226001"},
    "PATNA": {"lat": 25.5941, "lon": 85.1376, "state": "Bihar", "pin": "800001"},
    "MUZAFFARPUR": {"lat": 26.1209, "lon": 85.3647, "state": "Bihar", "pin": "842001"},
    "LUDHIANA": {"lat": 30.9010, "lon": 75.8573, "state": "Punjab", "pin": "141001"},
    "JAIPUR": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "pin": "302001"},
}


def generate_synthetic_borrower_dataset(count_per_district: int = 8) -> List[Borrower]:
    """Generate a realistic, synthetic MSME loan portfolio.

    Returns:
        List of Borrower models with explicit synthetic metadata.
    """
    borrowers: List[Borrower] = []
    sectors = list(BorrowerSector)

    # Realistic MSME enterprise profile templates
    enterprise_templates = [
        {"sector": BorrowerSector.AGRI_ALLIED, "alias": "Kisan Agri Inputs & Feed", "principal": 150000.0, "tenure": 24},
        {"sector": BorrowerSector.DAIRY_LIVESTOCK, "alias": "Kamdhenu Dairy Cooperative", "principal": 200000.0, "tenure": 36},
        {"sector": BorrowerSector.HANDLOOMS_TEXTILES, "alias": "Banaras Heritage Handlooms", "principal": 120000.0, "tenure": 18},
        {"sector": BorrowerSector.FOOD_PROCESSING, "alias": "Maa Annapurna Grain Mill", "principal": 350000.0, "tenure": 36},
        {"sector": BorrowerSector.RETAIL_MICRO_ENTERPRISE, "alias": "Shree Ram General Kirana", "principal": 80000.0, "tenure": 12},
        {"sector": BorrowerSector.SERVICES_LIGHT_MANUFACTURING, "alias": "Pawan Agro Electrical Works", "principal": 250000.0, "tenure": 24},
        {"sector": BorrowerSector.AGRI_ALLIED, "alias": "Surya Seed & Fertilizer Agency", "principal": 180000.0, "tenure": 24},
        {"sector": BorrowerSector.DAIRY_LIVESTOCK, "alias": "Gokul Chilling Unit", "principal": 300000.0, "tenure": 36},
    ]

    counter = 1001

    for district_name, geo_info in DISTRICT_COORDINATES.items():
        for i in range(count_per_district):
            tmpl = enterprise_templates[i % len(enterprise_templates)]
            b_id = f"SFL-SYN-{district_name[:3]}-{counter}"
            l_id = f"LN-SYN-{counter}"

            # Add minor spatial jitter within ~5km of district centroid
            jitter_lat = round(geo_info["lat"] + ((i * 7) % 11 - 5) * 0.008, 4)
            jitter_lon = round(geo_info["lon"] + ((i * 13) % 11 - 5) * 0.008, 4)

            principal = tmpl["principal"] + (i * 10000.0)
            tenure = tmpl["tenure"]
            # Approximate monthly EMI placeholder
            monthly_rate = DEFAULT_SYNTHETIC_INTEREST_RATE_PLACEHOLDER / 12.0
            emi_approx = round((principal * monthly_rate) / (1 - (1 + monthly_rate) ** (-tenure)), 2)

            loan = LoanSummary(
                loan_id=l_id,
                disbursed_principal=principal,
                current_outstanding_balance=round(principal * 0.75, 2),
                monthly_emi_amount=emi_approx,
                tenure_months_remaining=int(tenure * 0.75),
                currency=DEFAULT_CURRENCY,
            )

            geo = GeoLocation(
                latitude=jitter_lat,
                longitude=jitter_lon,
                district=district_name,
                state=geo_info["state"],
                pin_code=geo_info["pin"],
            )

            borrower = Borrower(
                borrower_id=b_id,
                anonymized_alias=f"{tmpl['alias']} ({district_name})",
                sector=tmpl["sector"],
                location=geo,
                active_loans=[loan],
                total_active_exposure=loan.current_outstanding_balance,
                contact_token=f"TOKEN_SYN_{b_id}",
            )
            borrowers.append(borrower)
            counter += 1

    return borrowers

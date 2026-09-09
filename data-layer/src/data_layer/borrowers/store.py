"""In-memory repository for synthetic borrower portfolios."""

from typing import Dict, List, Optional
from climateshield_shared.schemas.borrower import Borrower, BorrowerSector
from data_layer.baselines.interfaces import BorrowerRepository
from data_layer.borrowers.generator import generate_synthetic_borrower_dataset


class InMemoryBorrowerRepository(BorrowerRepository):
    """Borrower repository seeded with synthetic MSME demo records."""

    def __init__(self, borrowers: Optional[List[Borrower]] = None):
        self._borrowers: Dict[str, Borrower] = {}
        initial = borrowers if borrowers is not None else generate_synthetic_borrower_dataset()
        for b in initial:
            self._borrowers[b.borrower_id] = b

    async def list_borrowers_by_district(
        self,
        district_id: str,
        sector: Optional[BorrowerSector] = None,
    ) -> List[Borrower]:
        """Fetch active borrowers in a specific district, optionally filtered by sector."""
        dist_clean = district_id.strip().upper()
        results = [
            b for b in self._borrowers.values()
            if b.location.district.upper() == dist_clean
        ]
        if sector is not None:
            results = [b for b in results if b.sector == sector]
        return results

    async def get_borrower_by_id(
        self,
        borrower_id: str,
    ) -> Optional[Borrower]:
        """Fetch single borrower portfolio profile by unique ID."""
        return self._borrowers.get(borrower_id.strip())

    async def list_all_borrowers(self) -> List[Borrower]:
        """Return full borrower portfolio."""
        return list(self._borrowers.values())

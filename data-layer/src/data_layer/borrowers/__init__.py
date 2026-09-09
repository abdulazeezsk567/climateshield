"""Borrower package interfaces."""

from data_layer.borrowers.generator import generate_synthetic_borrower_dataset
from data_layer.borrowers.store import InMemoryBorrowerRepository

__all__ = [
    "generate_synthetic_borrower_dataset",
    "InMemoryBorrowerRepository",
]

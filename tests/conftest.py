import pandas as pd
import pytest


@pytest.fixture
def row():
    """Build one expense line, overriding only what a test cares about."""

    def _row(**overrides):
        line = {
            "date": pd.Timestamp("2025-01-10"),
            "montant": 100.0,
            "fournisseur": "Acme",
            "categorie": "Fournitures",
            "description": "achat courant",
            "statut": "valide",
        }
        return {**line, **overrides}

    return _row

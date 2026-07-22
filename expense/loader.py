"""Load and sanity-check an expense export."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = frozenset(
    {"date", "montant", "fournisseur", "categorie", "description", "statut"}
)
OPTIONAL_COLUMNS = frozenset({"employe", "centre_cout"})


def load_csv(path: str) -> pd.DataFrame:
    """Read an expense CSV and drop the rows that cannot be analysed.

    A missing column is fatal: the rules downstream all read by name, and a
    silently absent column would quietly disable a whole check. A single
    unparseable row is not fatal, it is dropped.

    Args:
        path: Path to the CSV export.

    Returns:
        The expenses, with `date` as datetimes and `montant` as numbers.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If any required column is missing.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    frame = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"colonnes manquantes: {', '.join(sorted(missing))}")

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["montant"] = pd.to_numeric(frame["montant"], errors="coerce")
    return frame.dropna(subset=["montant", "date"])

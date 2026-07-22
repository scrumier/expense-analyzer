import pandas as pd
import pytest

from expense.loader import load_csv

HEADER = "date,montant,fournisseur,categorie,description,statut"


def _csv(tmp_path, content):
    path = tmp_path / "expenses.csv"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_load_valid_csv(tmp_path):
    path = _csv(tmp_path, f"{HEADER}\n2025-01-15,234.50,Acme,Fournitures,Test,valide\n")

    df = load_csv(path)

    assert len(df) == 1
    assert df.iloc[0]["montant"] == 234.50
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_missing_column_raises(tmp_path):
    path = _csv(tmp_path, "date,montant,fournisseur\n2025-01-15,100,Acme\n")

    with pytest.raises(ValueError, match="colonnes manquantes"):
        load_csv(path)


def test_missing_column_is_named_in_the_error(tmp_path):
    path = _csv(tmp_path, "date,montant,fournisseur\n2025-01-15,100,Acme\n")

    with pytest.raises(ValueError, match="categorie"):
        load_csv(path)


def test_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        load_csv("/nonexistent/path.csv")


def test_unparseable_rows_are_dropped_not_fatal(tmp_path):
    path = _csv(
        tmp_path,
        f"{HEADER}\n"
        "2025-01-15,234.50,Acme,Fournitures,ok,valide\n"
        "2025-01-16,pas-un-nombre,Acme,Fournitures,cassé,valide\n"
        "pas-une-date,100.0,Acme,Fournitures,cassé,valide\n",
    )

    df = load_csv(path)

    assert len(df) == 1

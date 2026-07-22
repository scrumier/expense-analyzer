from unittest.mock import MagicMock, patch

import pytest

from expense.reporter import (
    _as_badge,
    _md_to_html,
    _narrative,
    _sorted_totals,
    generate_report,
)

SUMMARY = {
    "total_lignes": 2,
    "total_depenses": 350.0,
    "periode": "2025-01-01 - 2025-01-31",
    "par_categorie": {"A": 100.0, "B": 250.0},
    "top_fournisseurs": {"Acme": 350.0},
}


def _anomaly(**overrides):
    base = {
        "type": "montant_eleve",
        "date": "2025-01-12",
        "montant": 50_000.0,
        "fournisseur": "Acme",
        "categorie": "Fournitures",
        "description": "achat",
        "employe": "",
        "centre_cout": "",
        "detail": "Montant >= seuil 20,000 EUR",
        "score": None,
    }
    return {**base, **overrides}


def _mock_narrative(content):
    response = MagicMock()
    response.choices[0].message.content = content
    return patch(
        "expense.reporter.OpenAI",
        return_value=MagicMock(
            chat=MagicMock(
                completions=MagicMock(create=MagicMock(return_value=response))
            )
        ),
    )


def test_markdown_bold_becomes_strong():
    assert "<strong>total</strong>" in _md_to_html("le **total** grimpe")


def test_markdown_bullets_become_glyphs():
    assert "•" in _md_to_html("- premier point")


def test_markdown_table_becomes_a_table():
    html = _md_to_html("| Poste | Total |\n|---|---|\n| Voyage | 120 |")

    assert "<table" in html
    assert "<th>Poste</th>" in html
    assert "<td>Voyage</td>" in html


def test_html_in_the_commentary_is_escaped():
    html = _md_to_html("attention <script>alert(1)</script>")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_empty_model_response_raises():
    with _mock_narrative(None), pytest.raises(ValueError, match="aucune analyse"):
        _narrative(SUMMARY, [])


def test_badge_carries_a_colour_and_a_label():
    badged = _as_badge(_anomaly(type="doublon"))

    assert badged["badge_label"] == "Doublon"
    assert badged["badge_color"].startswith("#")


def test_unknown_anomaly_type_still_gets_a_badge():
    badged = _as_badge(_anomaly(type="type_inconnu"))

    assert badged["badge_label"] == "type_inconnu"
    assert badged["badge_color"].startswith("#")


def test_totals_are_ordered_biggest_first():
    assert _sorted_totals({"A": 10.0, "B": 30.0, "C": 20.0}) == [
        ("B", 30.0),
        ("C", 20.0),
        ("A", 10.0),
    ]


def test_report_escapes_supplier_names(tmp_path):
    output = tmp_path / "report.html"
    hostile = _anomaly(fournisseur="<script>alert(1)</script>")

    with _mock_narrative("Synthèse."):
        generate_report(SUMMARY, [hostile], str(output))

    html = output.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_report_renders_every_anomaly(tmp_path):
    output = tmp_path / "report.html"
    anomalies = [_anomaly(fournisseur="Un"), _anomaly(fournisseur="Deux")]

    with _mock_narrative("Synthèse."):
        generate_report(SUMMARY, anomalies, str(output))

    html = output.read_text(encoding="utf-8")
    assert "Un" in html
    assert "Deux" in html


def test_report_without_anomalies_says_so(tmp_path):
    output = tmp_path / "report.html"

    with _mock_narrative("Rien à signaler."):
        generate_report(SUMMARY, [], str(output))

    assert "Aucune anomalie" in output.read_text(encoding="utf-8")

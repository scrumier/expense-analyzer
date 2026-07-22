import pandas as pd

from expense.analyzer import detect_anomalies, summarize


def _of_type(anomalies, kind):
    return [a for a in anomalies if a["type"] == kind]


def test_amount_over_threshold_is_flagged(row):
    df = pd.DataFrame(
        [
            row(),
            row(date=pd.Timestamp("2025-01-11"), fournisseur="B"),
            row(date=pd.Timestamp("2025-01-12"), montant=50_000.0, fournisseur="X"),
        ]
    )

    flagged = _of_type(detect_anomalies(df, absolute_threshold=20_000), "montant_eleve")

    assert [a["montant"] for a in flagged] == [50_000.0]


def test_amount_under_threshold_is_not_flagged(row):
    df = pd.DataFrame([row(montant=19_999.0)])
    anomalies = detect_anomalies(df, absolute_threshold=20_000)

    assert _of_type(anomalies, "montant_eleve") == []


def test_same_charge_twice_in_the_window_is_flagged(row):
    df = pd.DataFrame(
        [
            row(date=pd.Timestamp("2025-03-10"), montant=847.5, fournisseur="Bureau"),
            row(date=pd.Timestamp("2025-03-12"), montant=847.5, fournisseur="Bureau"),
            row(date=pd.Timestamp("2025-04-01"), montant=200.0),
        ]
    )

    assert len(_of_type(detect_anomalies(df), "doublon")) >= 1


def test_same_charge_outside_the_window_is_not_flagged(row):
    df = pd.DataFrame(
        [
            row(date=pd.Timestamp("2025-03-01"), montant=847.5, fournisseur="Bureau"),
            row(date=pd.Timestamp("2025-06-01"), montant=847.5, fournisseur="Bureau"),
        ]
    )

    assert _of_type(detect_anomalies(df, duplicate_window_days=5), "doublon") == []


def test_a_duplicate_pair_is_reported_once(row):
    df = pd.DataFrame(
        [
            row(date=pd.Timestamp("2025-03-10"), montant=500.0, fournisseur="Bureau"),
            row(date=pd.Timestamp("2025-03-11"), montant=500.0, fournisseur="Bureau"),
            row(date=pd.Timestamp("2025-03-12"), montant=500.0, fournisseur="Bureau"),
        ]
    )

    assert len(_of_type(detect_anomalies(df), "doublon")) == 1


def test_model_isolates_the_outlier(row):
    lines = [
        row(date=pd.Timestamp(f"2025-02-{day:02d}"), montant=float(100 + day * 2))
        for day in range(3, 21)
        if pd.Timestamp(f"2025-02-{day:02d}").dayofweek < 5
    ]
    lines.append(
        row(date=pd.Timestamp("2025-03-03"), montant=95_000.0, fournisseur="Inconnu")
    )
    df = pd.DataFrame(lines)

    # Threshold pushed out of reach so the rule cannot claim it first.
    flagged = _of_type(detect_anomalies(df, absolute_threshold=200_000), "pattern_ml")

    assert 95_000.0 in [a["montant"] for a in flagged]


def test_model_does_not_run_on_a_tiny_dataset(row):
    df = pd.DataFrame([row(montant=float(i)) for i in range(5)])

    assert _of_type(detect_anomalies(df), "pattern_ml") == []


def test_a_line_caught_by_a_rule_is_not_reported_twice(row):
    lines = [
        row(date=pd.Timestamp(f"2025-02-{day:02d}"), montant=float(100 + day))
        for day in range(3, 21)
    ]
    lines.append(
        row(date=pd.Timestamp("2025-03-03"), montant=95_000.0, fournisseur="Inconnu")
    )
    df = pd.DataFrame(lines)

    anomalies = detect_anomalies(df, absolute_threshold=20_000)
    identities = [(a["date"], a["fournisseur"], a["montant"]) for a in anomalies]

    assert len(identities) == len(set(identities))


def test_the_same_export_gives_the_same_anomalies_twice(row):
    df = pd.DataFrame(
        [
            row(date=pd.Timestamp(f"2025-02-{day:02d}"), montant=float(100 + day * 7))
            for day in range(1, 26)
        ]
    )

    assert detect_anomalies(df) == detect_anomalies(df)


def test_summary_totals_the_period(row):
    df = pd.DataFrame(
        [
            row(date=pd.Timestamp("2025-01-01"), montant=100.0, categorie="A"),
            row(date=pd.Timestamp("2025-01-31"), montant=250.0, categorie="B"),
        ]
    )

    summary = summarize(df)

    assert summary["total_lignes"] == 2
    assert summary["total_depenses"] == 350.0
    assert summary["periode"] == "2025-01-01 - 2025-01-31"
    assert summary["par_categorie"] == {"A": 100.0, "B": 250.0}

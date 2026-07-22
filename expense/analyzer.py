"""Find the expense lines worth a human look.

Two layers, deliberately kept apart.

Fixed rules catch what is already known to be wrong: an amount over a
threshold, the same charge twice. They are auditable, and an accountant can
argue with the threshold.

Isolation Forest is an unsupervised model: it learns what normal looks like in
this particular dataset and isolates the points that take the fewest questions
to separate from the rest. It catches the combinations nobody wrote a rule for,
at the cost of not being able to state a threshold up front.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DEFAULT_ABSOLUTE_THRESHOLD = 20_000.0
DEFAULT_DUPLICATE_WINDOW_DAYS = 5
DEFAULT_CONTAMINATION = 0.08

# Isolation Forest needs a population to compare against. Under this many rows
# "unusual" is meaningless, so only the fixed rules run.
MIN_ROWS_FOR_MODEL = 10

# Fixed so two runs on the same export produce the same anomalies.
RANDOM_SEED = 42
N_ESTIMATORS = 100

# Thresholds used to phrase why a line was flagged, not to flag it.
RATIO_CATEGORY_HIGH = 3
SUPPLIER_RARE_MAX = 2
ROUND_AMOUNT_UNIT = 1000

# Saturday, in pandas' Monday=0 week numbering.
WEEKEND_START = 5

ANOMALY_FIELDS = ("fournisseur", "categorie", "description", "employe", "centre_cout")


def _row_identity(row: pd.Series) -> dict[str, object]:
    """Copy the descriptive columns of a row into an anomaly record.

    Args:
        row: One expense line.

    Returns:
        The date, amount and descriptive fields, with "" for anything absent.
    """
    return {
        "date": str(row["date"].date()),
        "montant": row["montant"],
        **{field: row.get(field, "") for field in ANOMALY_FIELDS},
    }


def _detect_rules(
    df: pd.DataFrame,
    absolute_threshold: float,
    duplicate_window_days: int,
) -> list[dict]:
    """Flag the lines that break an explicit rule.

    Args:
        df: The expenses.
        absolute_threshold: Amount at or above which a line is always flagged.
        duplicate_window_days: How far apart two identical charges can be and
            still count as a duplicate.

    Returns:
        One record per flagged line, with `score` left None: a rule either
        fires or it does not, there is no confidence to report.
    """
    anomalies = [
        {
            **_row_identity(row),
            "type": "montant_eleve",
            "detail": f"Montant >= seuil {absolute_threshold:,.0f} EUR",
            "score": None,
        }
        for _, row in df[df["montant"] >= absolute_threshold].iterrows()
    ]

    ordered = df.sort_values("date").reset_index(drop=True)
    already_reported: set[tuple] = set()
    for position, row in ordered.iterrows():
        key = (row["fournisseur"], row["montant"])
        if key in already_reported:
            continue
        twins = ordered[
            (ordered["fournisseur"] == row["fournisseur"])
            & (ordered["montant"] == row["montant"])
            & (abs((ordered["date"] - row["date"]).dt.days) <= duplicate_window_days)
            & (ordered.index != position)
        ]
        if twins.empty:
            continue
        already_reported.add(key)
        anomalies.append(
            {
                **_row_identity(row),
                "type": "doublon",
                "detail": (
                    f"Transaction identique le {twins.iloc[0]['date'].date()} "
                    f"({duplicate_window_days}j)"
                ),
                "score": None,
            }
        )

    return anomalies


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn expense lines into the numeric features the model reads.

    The amount is log-scaled because expenses span several orders of magnitude
    and the raw value would drown every other feature.

    Args:
        df: The expenses.

    Returns:
        One numeric row per expense line.
    """
    features = pd.DataFrame(index=df.index)
    features["montant_log"] = np.log1p(df["montant"])
    features["jour_semaine"] = df["date"].dt.dayofweek
    features["mois"] = df["date"].dt.month
    features["is_weekend"] = (df["date"].dt.dayofweek >= WEEKEND_START).astype(int)
    features["montant_rond"] = (df["montant"] % ROUND_AMOUNT_UNIT == 0).astype(int)

    category_mean = df.groupby("categorie")["montant"].transform("mean")
    features["ratio_cat"] = df["montant"] / category_mean.replace(0, 1)
    features["supplier_freq"] = df["fournisseur"].map(df["fournisseur"].value_counts())

    return features.fillna(0)


def _explain(row: pd.Series, feature_row: pd.Series, df: pd.DataFrame) -> str:
    """Put into words why the model isolated this line.

    The model gives a score, not a reason. These are the features that were
    extreme for this row, read back in plain language.

    Args:
        row: The flagged expense line.
        feature_row: Its computed features.
        df: The full dataset, used to quote the category average.

    Returns:
        A sentence listing what stands out, joined by "+".
    """
    reasons = []
    if feature_row["ratio_cat"] > RATIO_CATEGORY_HIGH:
        category_mean = df[df["categorie"] == row["categorie"]]["montant"].mean()
        reasons.append(
            f"montant {feature_row['ratio_cat']:.1f}x la moyenne de la "
            f"catégorie ({category_mean:.0f} EUR)"
        )
    if feature_row["is_weekend"]:
        reasons.append("transaction le weekend")
    if feature_row["montant_rond"]:
        reasons.append(f"montant rond multiple de {ROUND_AMOUNT_UNIT}")
    if feature_row["supplier_freq"] <= SUPPLIER_RARE_MAX:
        occurrences = int(feature_row["supplier_freq"])
        reasons.append(f"fournisseur peu fréquent ({occurrences} occurrence(s))")
    if not reasons:
        return "pattern inhabituel détecté par le modèle"
    return " + ".join(reasons)


def _detect_isolation_forest(df: pd.DataFrame, contamination: float) -> list[dict]:
    """Flag the lines the model considers atypical for this dataset.

    Args:
        df: The expenses.
        contamination: Share of the dataset the model should treat as
            anomalous. It is a budget, not a discovered truth.

    Returns:
        One record per flagged line, most anomalous first, each with a score
        from 0 to 1 where 1 is the most atypical line in this dataset.
    """
    if len(df) < MIN_ROWS_FOR_MODEL:
        return []

    features = _build_features(df)
    scaled = StandardScaler().fit_transform(features)

    model = IsolationForest(
        contamination=contamination,
        random_state=RANDOM_SEED,
        n_estimators=N_ESTIMATORS,
    )
    labels = model.fit_predict(scaled)
    raw_scores = model.score_samples(scaled)

    # score_samples is more negative the more anomalous. Flip and rescale to
    # 0-1 so the report can show a number that reads the intuitive way.
    lowest, highest = raw_scores.min(), raw_scores.max()
    normalised = 1 - (raw_scores - lowest) / (highest - lowest + 1e-9)

    anomalies = [
        {
            **_row_identity(df.iloc[index]),
            "type": "pattern_ml",
            "detail": _explain(df.iloc[index], features.iloc[index], df),
            "score": round(float(normalised[index]), 3),
        }
        for index in np.where(labels == -1)[0]
    ]
    anomalies.sort(key=lambda anomaly: -anomaly["score"])
    return anomalies


def detect_anomalies(
    df: pd.DataFrame,
    absolute_threshold: float = DEFAULT_ABSOLUTE_THRESHOLD,
    duplicate_window_days: int = DEFAULT_DUPLICATE_WINDOW_DAYS,
    contamination: float = DEFAULT_CONTAMINATION,
) -> list[dict]:
    """Run both detection layers and merge their findings.

    A line already caught by a rule is not reported twice: the rule explains
    it better than a model score would.

    Args:
        df: The expenses.
        absolute_threshold: Amount at or above which a line is always flagged.
        duplicate_window_days: Window for treating two identical charges as a
            duplicate.
        contamination: Share of the dataset the model treats as anomalous.

    Returns:
        Rule hits first, then the model's, without duplicates.
    """
    rules = _detect_rules(df, absolute_threshold, duplicate_window_days)
    model_hits = _detect_isolation_forest(df, contamination)

    seen = {(a["date"], a["fournisseur"], a["montant"]) for a in rules}
    unique = [
        a for a in model_hits if (a["date"], a["fournisseur"], a["montant"]) not in seen
    ]
    return rules + unique


def summarize(df: pd.DataFrame) -> dict:
    """Total the expenses for the report header.

    Args:
        df: The expenses.

    Returns:
        Totals overall, by category and by top supplier, plus by employee and
        cost centre when those columns are present.
    """
    summary = {
        "total_lignes": len(df),
        "total_depenses": round(df["montant"].sum(), 2),
        "periode": f"{df['date'].min().date()} - {df['date'].max().date()}",
        "par_categorie": df.groupby("categorie")["montant"].sum().round(2).to_dict(),
        "top_fournisseurs": (
            df.groupby("fournisseur")["montant"].sum().nlargest(5).round(2).to_dict()
        ),
    }
    if "employe" in df.columns:
        summary["par_employe"] = (
            df.groupby("employe")["montant"].sum().round(2).to_dict()
        )
    if "centre_cout" in df.columns:
        summary["par_centre_cout"] = (
            df.groupby("centre_cout")["montant"].sum().round(2).to_dict()
        )
    return summary

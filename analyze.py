#!/usr/bin/env python3
"""Analyse an expense CSV and write an HTML report.

Usage:
    uv run python analyze.py demo_data/expenses.csv output/
"""

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from expense.analyzer import (
    DEFAULT_ABSOLUTE_THRESHOLD,
    DEFAULT_CONTAMINATION,
    DEFAULT_DUPLICATE_WINDOW_DAYS,
    detect_anomalies,
    summarize,
)
from expense.loader import load_csv
from expense.reporter import generate_report


@dataclass(frozen=True)
class Analysis:
    """What one run produced."""

    report_path: str
    stats: dict
    anomalies: list[dict]
    row_count: int


def _parse_args() -> argparse.Namespace:
    """Read the command line.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Analyse an expense CSV.")
    parser.add_argument("csv_path", help="Expense CSV to analyse")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="output",
        help="Where to write the report (default: output/)",
    )
    parser.add_argument(
        "--seuil-absolu",
        type=float,
        default=DEFAULT_ABSOLUTE_THRESHOLD,
        help="Amount at or above which a line is always flagged",
    )
    parser.add_argument(
        "--fenetre-doublon",
        type=int,
        default=DEFAULT_DUPLICATE_WINDOW_DAYS,
        help="Days within which two identical charges count as a duplicate",
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=DEFAULT_CONTAMINATION,
        help="Share of the dataset the model treats as anomalous",
    )
    return parser.parse_args()


def run(
    csv_path: str,
    output_dir: str,
    *,
    absolute_threshold: float = DEFAULT_ABSOLUTE_THRESHOLD,
    duplicate_window_days: int = DEFAULT_DUPLICATE_WINDOW_DAYS,
    contamination: float = DEFAULT_CONTAMINATION,
) -> Analysis:
    """Load, analyse and report, in one pass.

    Args:
        csv_path: Expense CSV to analyse.
        output_dir: Directory the report is written to, created if missing.
        absolute_threshold: Amount at or above which a line is always flagged.
        duplicate_window_days: Window for treating two charges as duplicates.
        contamination: Share of the dataset the model treats as anomalous.

    Returns:
        The report path and everything the caller might want to print.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    expenses = load_csv(csv_path)
    anomalies = detect_anomalies(
        expenses,
        absolute_threshold=absolute_threshold,
        duplicate_window_days=duplicate_window_days,
        contamination=contamination,
    )
    stats = summarize(expenses)

    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M")
    report_path = generate_report(
        stats,
        anomalies,
        str(Path(output_dir) / f"rapport-depenses-{timestamp}.html"),
    )
    return Analysis(
        report_path=report_path,
        stats=stats,
        anomalies=anomalies,
        row_count=len(expenses),
    )


def main() -> None:
    """Run the analysis from the command line and report what it found."""
    args = _parse_args()

    print(f"Analyse de {args.csv_path}...")
    result = run(
        args.csv_path,
        args.output_dir,
        absolute_threshold=args.seuil_absolu,
        duplicate_window_days=args.fenetre_doublon,
        contamination=args.contamination,
    )

    print(f"  {result.row_count} lignes chargées")
    print(f"  {len(result.anomalies)} anomalies détectées")
    for anomaly in result.anomalies:
        print(
            f"    [{anomaly['type']}] {anomaly['date']} "
            f"{anomaly['fournisseur']} {anomaly['montant']:,.2f} EUR"
        )

    print(f"\nRapport: {result.report_path}")
    print(f"Total dépenses: {result.stats['total_depenses']:,.2f} EUR")
    print(f"Période: {result.stats['periode']}")


if __name__ == "__main__":
    main()

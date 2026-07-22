"""Serve the latest expense report, and generate one on demand."""

import logging
import os
from pathlib import Path

from flask import Flask, Response, render_template, send_file

from analyze import run

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = BASE_DIR / "demo_data" / "expenses.csv"

REPORT_GLOB = "rapport-depenses-*.html"

log = logging.getLogger(__name__)


def latest_report() -> Path | None:
    """Find the most recent report on disk.

    Reports are named with a sortable timestamp, so the last one by name is
    the last one written.

    Returns:
        Path to the newest report, or None if none has been generated.
    """
    reports = sorted(OUTPUT_DIR.glob(REPORT_GLOB))
    return reports[-1] if reports else None


@app.route("/")
def index() -> Response | str:
    """Show the latest report, or offer to generate one.

    Returns:
        The report, or the landing page.
    """
    report = latest_report()
    if report:
        return send_file(report)
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate() -> Response | tuple[str, int]:
    """Run the analysis on the demo data and show the result.

    Returns:
        The freshly written report, or an error page if the run failed.
    """
    try:
        result = run(str(CSV_PATH), str(OUTPUT_DIR))
    except (OSError, ValueError):
        log.exception("Report generation failed")
        return render_template("error.html"), 500
    return send_file(result.report_path)


def main() -> None:
    """Serve the app on the configured host and port."""
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT") or 5051),
        debug=False,
    )


if __name__ == "__main__":
    main()

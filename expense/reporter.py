"""Turn the analysis into an HTML report a finance team can read.

The numbers come from the rules and the model. The model only writes the
commentary around them: it is never asked what is anomalous, only to phrase
what was already found.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
MAX_TOKENS = 1500

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

BADGE_COLORS = {
    "montant_eleve": "#dc2626",
    "doublon": "#d97706",
    "pattern_ml": "#7c3aed",
}
BADGE_LABELS = {
    "montant_eleve": "Seuil absolu",
    "doublon": "Doublon",
    "pattern_ml": "Pattern ML",
}
BADGE_DEFAULT_COLOR = "#6b7280"

SYSTEM_PROMPT = (
    "Tu es un analyste financier interne. Rédige un rapport d'audit en "
    "français, professionnel et concis. Structure: 1) Synthèse (2 phrases), "
    "2) Anomalies détectées (une ligne par anomalie, explication métier "
    "claire), 3) Recommandations (2-3 actions concrètes). Ton direct, pas de "
    "jargon inutile."
)

_TABLE_SEPARATOR = re.compile(r"[\s|:-]+$")


def _narrative(summary: dict, anomalies: list[dict]) -> str:
    """Ask the model to comment on what the analysis found.

    Args:
        summary: Totals for the period.
        anomalies: Every flagged line, with the reason it was flagged.

    Returns:
        The commentary, in Markdown.

    Raises:
        ValueError: If the model returned an empty response. A report with a
            blank analysis section looks finished and is not.
    """
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Resume des depenses:\n"
                    f"{json.dumps(summary, ensure_ascii=False, indent=2)}\n\n"
                    f"Anomalies detectees:\n"
                    f"{json.dumps(anomalies, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Le modèle n'a renvoyé aucune analyse.")
    return content


def _render_markdown_table(lines: list[str], start: int) -> tuple[str, int]:
    """Convert one Markdown table into HTML.

    Args:
        lines: Every line of the commentary, already escaped.
        start: Index of the table's header row.

    Returns:
        The table markup, and the index of the first line after the table.
    """
    headers = [cell.strip() for cell in lines[start].strip().strip("|").split("|")]
    html = [
        "<table class='md-table'><thead><tr>",
        "".join(f"<th>{header}</th>" for header in headers),
        "</tr></thead><tbody>",
    ]

    index = start + 2  # skip the header and the |---|---| separator
    while index < len(lines) and "|" in lines[index]:
        cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        html.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        index += 1

    html.append("</tbody></table>")
    return "".join(html), index


def _md_to_html(text: str) -> Markup:
    """Render the model's Markdown commentary as HTML.

    The text is escaped before any markup is added, so the commentary can only
    produce the tags this function puts there itself.

    Args:
        text: Commentary in Markdown.

    Returns:
        Safe HTML.
    """
    lines = str(escape(text)).split("\n")

    rendered: list[str] = []
    index = 0
    while index < len(lines):
        is_table_header = (
            "|" in lines[index]
            and index + 1 < len(lines)
            and _TABLE_SEPARATOR.match(lines[index + 1].replace("|", ""))
        )
        if is_table_header:
            table, index = _render_markdown_table(lines, index)
            rendered.append(table)
            continue
        rendered.append(lines[index])
        index += 1

    html = "\n".join(rendered)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"^#{1,3} (.+)$", r"<strong>\1</strong>", html, flags=re.MULTILINE)
    html = re.sub(r"^- (.+)$", r"• \1", html, flags=re.MULTILINE)
    return Markup(html.replace("\n\n", "<br><br>").replace("\n", "<br>"))


def _as_badge(anomaly: dict) -> dict:
    """Attach the badge colour and label an anomaly is displayed with.

    Args:
        anomaly: One flagged line.

    Returns:
        The anomaly, plus `badge_color` and `badge_label`.
    """
    return {
        **anomaly,
        "badge_color": BADGE_COLORS.get(anomaly["type"], BADGE_DEFAULT_COLOR),
        "badge_label": BADGE_LABELS.get(anomaly["type"], anomaly["type"]),
    }


def _sorted_totals(totals: dict[str, float]) -> list[tuple[str, float]]:
    """Order a breakdown by descending amount.

    Args:
        totals: Amount per label.

    Returns:
        Label and amount pairs, biggest first.
    """
    return sorted(totals.items(), key=lambda item: -item[1])


def generate_report(summary: dict, anomalies: list[dict], output_path: str) -> str:
    """Write the HTML report.

    Args:
        summary: Totals for the period.
        anomalies: Every flagged line.
        output_path: Where to write the report.

    Returns:
        The path that was written.
    """
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    html = environment.get_template("report.html").render(
        generated_at=datetime.now().astimezone(),
        summary=summary,
        anomalies=[_as_badge(anomaly) for anomaly in anomalies],
        narrative=_md_to_html(_narrative(summary, anomalies)),
        par_categorie=_sorted_totals(summary["par_categorie"]),
        par_employe=_sorted_totals(summary.get("par_employe", {})),
        par_centre_cout=_sorted_totals(summary.get("par_centre_cout", {})),
    )
    Path(output_path).write_text(html, encoding="utf-8")
    return output_path

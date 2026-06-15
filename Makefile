# expense-analyzer — launcher autonome.
#   make setup   <- une fois : venv + deps + génère le rapport de démo
#   make run     <- démarre la visualisation  ->  http://127.0.0.1:5051
# Bind Tailscale uniquement, jamais exposé publiquement.

-include local.mk
TS ?= 127.0.0.1
PORT := 5051

.PHONY: help setup run

help:
	@echo ""
	@echo "  expense-analyzer   ->  http://$(TS):$(PORT)"
	@echo "    make setup   deps + génère le rapport (une fois)"
	@echo "    make run     démarre la démo"
	@echo ""

setup:
	@echo "==> uv sync..."
	@uv sync --quiet
	@echo "==> Génère le rapport de démo..."
	@uv run python analyze.py demo_data/expenses.csv output/
	@echo "==> Prêt. Lancer :  make run"

run:
	@test -n "$$(ls output/rapport-depenses-*.html 2>/dev/null)" || \
	  ( echo "==> Rapport manquant, génération..."; uv run python analyze.py demo_data/expenses.csv output/ )
	@echo ""
	@echo "==> Ouvre sur ton Mac :  http://$(TS):$(PORT)      (Ctrl+C pour arrêter)"
	@echo ""
	@FLASK_HOST=$(TS) FLASK_PORT=$(PORT) uv run python app.py

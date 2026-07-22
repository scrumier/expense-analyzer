# expense-analyzer
#   make setup    install dependencies (once)
#   make run      serve the report, with a button to generate it
#   make report   generate a report from the demo data, on the command line
#   make demo     regenerate the demo CSV
#   make test     run the test suite
#   make lint     lint and format check

-include local.mk
HOST ?= 127.0.0.1
PORT ?= 5051
CSV ?= demo_data/expenses.csv
OUT ?= output

.PHONY: help setup run report demo test lint

help:
	@echo ""
	@echo "  make setup    install dependencies"
	@echo "  make run      report viewer  ->  http://$(HOST):$(PORT)"
	@echo "  make report   generate a report from $(CSV)"
	@echo "  make demo     regenerate the demo CSV"
	@echo "  make test     run the test suite"
	@echo "  make lint     lint and format check"
	@echo ""

setup:
	@uv sync --quiet
	@echo "==> Ready. Copy .env.example to .env and add your OPENROUTER_API_KEY."

run:
	@echo "==> http://$(HOST):$(PORT)   (Ctrl+C to stop)"
	@FLASK_HOST=$(HOST) FLASK_PORT=$(PORT) uv run python app.py

report:
	@uv run python analyze.py $(CSV) $(OUT)

demo:
	@uv run python demo_data/gen_expenses.py

test:
	@uv run pytest -q

lint:
	@uv run ruff check .
	@uv run ruff format --check .

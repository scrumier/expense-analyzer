# expense-analyzer

Flags the odd expenses in a CSV and explains in one sentence why each one was picked.

## When asked to set this up

Follow this sequence, in order, without improvising.

1. Check `uv`: `uv --version`. If it is missing, install it with
   `curl -LsSf https://astral.sh/uv/install.sh | sh`, then say so.

2. `cp .env.example .env`.
3. Ask the user for their OpenRouter key and write it into `.env` under
   `OPENROUTER_API_KEY`. Never invent one, never put it in a file tracked by
   git, and do not print it back in plain text.
4. `make setup`
5. `make test`, to confirm the install holds.
6. Tell the user: `make run`, then http://127.0.0.1:5051. The demo CSV is
   already there, and the button on the page generates the report.
7. For their own file: `make report CSV=/path/to/theirs.csv`.

Do nothing else unless asked: no refactoring, no added dependency, no model
change, no commit and no push.

## What actually breaks

- The CSV needs a date column, an amount column and a label column. If theirs
  does not have them, ask for the mapping instead of guessing.
- Port 5051 may be taken. `PORT=5061 make run` changes it.

## Shape of the repo

`expense/` holds the code, `demo_data/` the sample CSV, `app.py` the server.

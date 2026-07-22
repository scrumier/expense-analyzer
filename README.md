# expense-analyzer

**Problem:** at month-end you scroll the expense sheet hoping something looks wrong.<br>
**Solution:** the suspicious lines get flagged, each one with the reason why.

Output is an HTML report, written in sentences you can forward to the person concerned.

## Run it

```bash
cp .env.example .env    # add your OPENROUTER_API_KEY
make setup              # deps, then generates the demo report
make run                # http://127.0.0.1:5051
```

Or straight to the report:

```bash
uv run python analyze.py demo_data/expenses.csv output/
```

Your CSV needs these columns: `date`, `montant`, `fournisseur`, `categorie`, `description`, `statut`.

## How it works

Two layers, on purpose.

**Fixed rules** catch what you already know is wrong: amount over a threshold, exact duplicate within a time window. Auditable, no surprises.

**Isolation Forest** learns what normal looks like in your own data and catches what no rule anticipated: a rare supplier, on a weekend, for a suspiciously round number. Each hit comes with a confidence score.

Then Claude writes the narration so the report reads like a note, not a dump.

Tune it with `--seuil-absolu`, `--fenetre-doublon` and `--contamination`.

## What it won't do

It doesn't decide that something is fraud. It says "this one is unusual, and here's why". A human decides.

## This is the level 1

One CSV you export by hand.

What's actually useful is the same thing pulled from your ERP on a schedule, with thresholds tuned on your own history instead of my defaults, and the report landing in the right inbox on the 1st without anyone launching it. That's the part I build.

[LinkedIn](https://www.linkedin.com/in/sonam-crumiere) · [sonam.me](https://sonam.me)

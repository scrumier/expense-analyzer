# expense-analyzer

Agent d'analyse de dépenses d'entreprise. Détecte automatiquement les anomalies financières et génère un rapport HTML avec explication IA.

## Ce que ça fait

1. Charge un CSV de dépenses (export ERP, notes de frais, etc.)
2. Détecte les anomalies avec deux approches combinées:
   - **Règles métier**: seuil absolu configurable, doublons exacts
   - **Isolation Forest** (machine learning): patterns inhabituels détectés sans règles prédéfinies
3. Génère un rapport HTML avec narration en langage naturel via Claude

## Utilisation

```bash
# Setupx
uv sync
cp .env.example .env  # remplir OPENROUTER_API_KEY

# Générer les données de démo
uv run python demo_data/gen_expenses.py

# Analyser
uv run python analyze.py demo_data/expenses.csv output/
# → ouvrir output/rapport-depenses-*.html
```

## Paramètres

```bash
uv run python analyze.py expenses.csv output/ \
  --seuil-absolu 15000 \     # montant au-dessus duquel on flag systématiquement
  --fenetre-doublon 7 \      # jours pour considérer deux transactions comme doublons
  --contamination 0.05       # % de transactions à considérer comme anomalies (IF)
```

## Format CSV attendu

Colonnes requises: `date`, `montant`, `fournisseur`, `categorie`, `description`, `statut`

## Architecture

```
analyze.py              → CLI entry point
expense/
  loader.py             → lecture et validation CSV
  analyzer.py           → détection anomalies (règles + Isolation Forest)
  reporter.py           → rapport HTML + narration Claude via OpenRouter
demo_data/
  gen_expenses.py       → génère 203 lignes avec 5 anomalies injectées
```

## Anomalies détectées

**Règles fixes (auditables):**
- Montant >= seuil absolu
- Doublon exact (même fournisseur, même montant, fenêtre configurable)

**Isolation Forest (non-supervisé):**
- Apprend ce qui est "normal" dans vos propres données
- Détecte les combinaisons inhabituelles: fournisseur rare + weekend + montant rond
- Score de confiance 0-1 affiché dans le rapport

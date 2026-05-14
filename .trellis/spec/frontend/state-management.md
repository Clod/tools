# State Management (Marimo)

> How state is managed in Marimo notebooks.

---

## Overview

This project uses **Marimo** for UI. State management is cell-based and reactive — there is no Redux, Zustand, or React context. Each cell's output is its "state", and downstream cells automatically re-run when inputs change.

---

## State Categories

### UI Widget State (local, reactive)

Widget values are the primary state mechanism:

```python
# Define widget
date_filter = mo.ui.date_range(label="Período")

# Consume in another cell — re-runs when date_filter.value changes
start, end = date_filter.value
```

### Computed/Derived State

DataFrames derived from widgets or DB queries — recomputed reactively:

```python
@app.cell
def _(engine, date_filter):
    # Derived from widget + DB connection
    df = pd.read_sql(f"SELECT ... WHERE date >= '{date_filter.value[0]}'", engine)
    return df,
```

### Configuration State (static)

Constants loaded once at startup and never changed:

```python
env_path = os.path.abspath(os.path.join(os.getcwd(), "../marimo_lab/.env"))
load_dotenv(env_path)
DB_SERVER = os.getenv("DB_SERVER")
```

---

## When to Promote to a Separate Cell

Extract state to its own cell when:
- Multiple downstream cells need the same value
- The computation is expensive (DB query, file load)
- It involves user input (always a `mo.ui.*` widget)

---

## Server State (DB Data)

DB-fetched DataFrames are re-fetched on every relevant filter change — there is no caching layer. For expensive queries, keep the filter widgets coarse-grained to avoid excessive re-fetching.

---

## Anti-Patterns

- **Global mutable variables**: Don't use module-level mutable state that cells modify — it breaks reactivity
- **Storing state in files**: Don't write intermediate results to disk as a state mechanism
- **Sharing state via side effects**: All inter-cell communication must go through return values

---

## Examples

- Widget + derived state: `csv_analizer/primary_scores.py` (dir_input → load CSV → display)
- Multi-step state: `marimo_lab/sentiance_data_explorer.py` (filter → query → table → row select → inspector)

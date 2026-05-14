# Hook Guidelines (Marimo Reactive Patterns)

> How reactive data flow is handled in Marimo notebooks.

---

## Overview

This project uses **Marimo** instead of React. There are no React hooks. Marimo's reactivity is cell-based — when a cell's inputs change, dependent cells automatically re-run.

---

## Marimo Reactive Pattern (Equivalent to Hooks)

In Marimo, a cell declares its dependencies via function parameters:

```python
@app.cell
def _(mo, engine):
    # This cell re-runs whenever `engine` or `mo` changes
    df = pd.read_sql("SELECT ...", engine)
    return df,
```

The function signature acts like a dependency array in `useEffect`.

---

## UI Widgets as State

Marimo `mo.ui.*` widgets hold reactive state. When a widget changes, dependent cells re-run:

```python
@app.cell
def _(mo):
    # Widget definition — acts like useState
    date_filter = mo.ui.date_range(label="Rango de fechas")
    return date_filter,

@app.cell
def _(date_filter, engine):
    # Reactive to date_filter changes — acts like useEffect
    start, end = date_filter.value
    df = pd.read_sql(f"SELECT ... WHERE date BETWEEN '{start}' AND '{end}'", engine)
    return df,
```

---

## Common Widget Patterns

```python
# Text input (search/path)
text_input = mo.ui.text(placeholder="Ingresa el directorio...", label="Directorio CSV")

# Dropdown
selector = mo.ui.dropdown(options=["opcion_a", "opcion_b"], label="Tipo")

# Date range
date_range = mo.ui.date_range(label="Período")

# Number slider
threshold = mo.ui.slider(start=0, stop=100, value=50, label="Umbral mínimo")

# Checkbox
include_nulls = mo.ui.checkbox(label="Incluir nulls")
```

---

## Data Fetching Pattern

Wrap DB queries reactively — no manual refresh needed:

```python
@app.cell
def _(engine, user_filter):
    if engine is None:
        return pd.DataFrame(),
    
    user_id = user_filter.value
    query = f"SELECT * FROM SentianceEventos WHERE UsuarioID = '{user_id}' ORDER BY Fecha DESC"
    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        df = pd.DataFrame({"error": [str(e)]})
    return df,
```

---

## Naming Conventions

- Widget variables: `snake_case` describing what it filters/controls (`date_filter`, `user_selector`, `dir_input`)
- DataFrames: `df_<source>` for raw data (`df_csv`, `df_sql`), plain `df` or `result_df` for processed
- Cell functions: descriptive names or `_()` for anonymous

---

## Common Mistakes

- **Circular dependencies**: Cell A depends on Cell B which depends on Cell A — Marimo will error
- **Mutating returned values**: Returned variables from cells should not be mutated elsewhere
- **Heavy computation in widget callbacks**: Compute in a dedicated cell, not in the widget definition

---

## Examples

- Reactive filtering: `csv_analizer/primary_scores.py` (dir_input + data loading cells)
- Row selection drill-down: `marimo_lab/sentiance_data_explorer.py`

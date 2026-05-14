# Component Guidelines (Marimo UI)

> How Marimo UI elements are composed in this project.

---

## Overview

The "components" in this project are Marimo UI widgets (`mo.ui.*`) and layout primitives (`mo.vstack`, `mo.hstack`, `mo.accordion`). There are no React components.

---

## Standard Cell Structure

Each `@app.cell` function follows this pattern:

```python
@app.cell
def _(mo, df):
    # 1. Compute or filter data
    filtered = df[df["score"] > 0.5]

    # 2. Build UI elements
    table = mo.ui.table(filtered, pagination=True, max_height=500)

    # 3. Compose layout
    return mo.vstack([
        mo.md("## Filtered Results"),
        table,
    ])
```

---

## Table Display

**Always** wrap DataFrames in `mo.ui.table()`. Never return a raw DataFrame.

```python
# CORRECT
mo.ui.table(df, pagination=True, max_height=500, selection=None)

# WRONG
df  # raw DataFrame — do not do this
```

Common options:
- `pagination=True` — enable pagination for large datasets
- `max_height=500` — prevent overflow
- `selection="single"` — enable row selection for drill-down
- `selection=None` — display-only table

---

## Layout Patterns

```python
# Vertical stack (title + table, sections)
mo.vstack([title_md, table_widget])

# Horizontal stack (filters side by side)
mo.hstack([filter_a, filter_b, filter_c])

# Collapsible technical details
mo.accordion({
    "Raw JSON": mo.ui.text_area(value=json.dumps(data, indent=2), disabled=True),
    "Query Log": mo.md(f"```sql\n{query}\n```"),
})
```

---

## Callouts for Status

Use `mo.callout()` for operational feedback instead of `print()`:

```python
mo.callout("✅ Conexión exitosa a la base de datos", kind="success")
mo.callout("⚠️ No se encontraron registros para el filtro", kind="warn")
mo.callout("❌ Error al cargar el archivo CSV", kind="danger")
mo.callout("ℹ️ Selecciona un viaje para ver el detalle", kind="info")
```

---

## JSON Inspector Pattern

For drill-down into a selected row's JSON:

```python
@app.cell
def _(table_with_selection, mo, json):
    selected = table_with_selection.value
    if selected is not None and len(selected) > 0:
        raw = selected[0].get("JSON", "{}")
        parsed = json.loads(raw)
        inspector = mo.ui.text_area(
            value=json.dumps(parsed, indent=2, ensure_ascii=False),
            disabled=True,
            rows=20,
        )
    else:
        inspector = mo.callout("Selecciona una fila para ver el detalle", kind="info")
    return inspector
```

---

## Anti-Patterns

- **NEVER** return raw DataFrames — always wrap with `mo.ui.table()`
- **NEVER** use `print()` for user feedback — use `mo.callout()` or `mo.md()`
- **NEVER** put heavy computation inside the return statement — compute first, then return UI
- **NEVER** create global mutable state between cells — use cell return values

---

## Examples

- Full UI composition: `marimo_lab/sentiance_data_explorer.py`
- Table + accordion pattern: `csv_analizer/primary_scores.py`

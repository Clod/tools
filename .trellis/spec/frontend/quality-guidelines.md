# Quality Guidelines (Marimo/UI)

> Code quality standards for Marimo notebooks and UI code.

---

## Overview

Quality in Marimo notebooks means: correct reactivity, clean cell decomposition, proper UI feedback, and safe data display.

---

## Required Patterns

- **`/// script` metadata** in every Marimo file with `requires-python` and `dependencies`
- **`app = marimo.App(width="full")`** for data-heavy notebooks
- **`mo.ui.table()`** to display all DataFrames — never return raw DataFrames
- **`mo.callout()`** for status messages — never `print()`
- **`mo.accordion`** for technical/debug details that should be collapsible

---

## Forbidden Patterns

| Pattern | Why |
|---------|-----|
| Raw DataFrame return from cell | No pagination, no UX, breaks layout |
| `print()` in cells | Not shown in app mode, use `mo.md()` or `mo.callout()` |
| Hardcoded absolute paths | Breaks on other machines |
| Mutable module-level state | Breaks Marimo reactivity |
| Cells > 50 lines | Split into focused cells |

---

## Cell Decomposition Rules

Each cell should do one thing:
1. **Import cell**: imports only
2. **Config cell**: env vars, constants
3. **Connection cell**: DB engine setup
4. **Filter cell**: UI widgets
5. **Query cell**: DB query reactive to filters
6. **Display cell**: `mo.ui.table()` + layout

---

## Documentation

Every Marimo notebook file must have a module-level docstring that includes:
- What the notebook does
- Required inputs (CSV files, env vars)
- How to run it (`uvx marimo run`, `uvx marimo edit`)

---

## Running and Testing

```bash
# Interactive edit mode
uvx marimo edit notebook.py

# App/run mode (final output only)
uvx marimo run notebook.py

# Batch execution (non-interactive)
uv run notebook.py
```

---

## Code Review Checklist

- [ ] `/// script` metadata present
- [ ] Module docstring explains purpose and how to run
- [ ] DataFrames displayed via `mo.ui.table()` with pagination
- [ ] No hardcoded credentials or absolute paths
- [ ] Cell functions are focused (one responsibility)
- [ ] Status feedback uses `mo.callout()` not `print()`
- [ ] Layout uses `mo.vstack`/`mo.hstack` for composition

---

## Examples

- Model notebook quality: `csv_analizer/primary_scores.py`
- Full-featured notebook: `marimo_lab/sentiance_data_explorer.py`

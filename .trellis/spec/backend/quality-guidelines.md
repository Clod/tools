# Quality Guidelines

> Code quality standards for Python data scripts and Marimo notebooks.

---

## Overview

This is a Python data analytics project. Quality focuses on correctness, reproducibility, and maintainability of data pipelines and notebooks.

---

## Required Patterns

- **`/// script` metadata block** in every Marimo notebook declaring `requires-python` and `dependencies`
- **Environment isolation** via `uv` — never rely on global Python packages
- **`.env` for credentials** — never hardcode DB passwords or API keys
- **Per-row JSON error handling** — never crash on a single bad row
- **`pd.merge` for multi-source joins** — always rename overlapping columns for clarity

---

## Forbidden Patterns

| Pattern | Why |
|---------|-----|
| Hardcoded DB credentials | Security risk, breaks on other machines |
| `except: pass` | Silent failures hide bugs |
| Raw DataFrame display without `mo.ui.table()` | Poor UX in Marimo |
| SQL Server JSON functions | Inconsistent, use pandas `json.loads()` instead |
| Global mutable state between cells | Breaks Marimo reactivity |
| `print()` for user feedback in Marimo | Use `mo.callout()` or `mo.md()` |
| Modifying the DB | It is read-only — any write attempt is a critical error |

---

## Marimo-Specific Rules

- Always use `app = marimo.App(width="full")` for data-heavy notebooks
- Wrap DataFrames: `mo.ui.table(df, pagination=True, max_height=500)`
- Use `mo.accordion` for collapsible technical details (raw JSON, logs)
- Layout: `mo.vstack([title, table])`, `mo.hstack([filter_a, filter_b])`

---

## File Size

- Marimo cells: keep under 50 lines per cell
- Scripts: no hard limit, but extract reusable logic into helper functions

---

## Dependency Management

- Each project subdirectory with notebooks has its own `pyproject.toml`
- Pin versions in `pyproject.toml` for reproducibility
- Use `uv` to run notebooks: `uvx marimo run notebook.py`

---

## Code Review Checklist

- [ ] No hardcoded credentials
- [ ] `/// script` metadata present in Marimo notebooks
- [ ] JSON parsed per-row with error handling
- [ ] DataFrames displayed via `mo.ui.table()`, not raw
- [ ] Overlapping columns renamed after `pd.merge`
- [ ] No writes to the database
- [ ] `.env` path uses relative `os.path.join` (not absolute)

---

## Examples

- Correct notebook structure: `csv_analizer/primary_scores.py`
- Full layout patterns: `marimo_lab/sentiance_data_explorer.py`

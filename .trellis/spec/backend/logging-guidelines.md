# Logging Guidelines

> How logging is done in this project.

---

## Overview

This project uses Python's standard `logging` module. In Marimo notebooks, logging is primarily supplemented by Marimo's UI feedback components (`mo.callout`, `mo.md`).

---

## Setup Pattern

Standard logging configuration used in scripts:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("module_name")
```

Use a module-specific logger name (e.g., `"sentiance_analyzer"`, `"primary_scores"`).

---

## Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed parsing steps, intermediate values during development |
| `INFO` | Successful operations: connected to DB, loaded CSV, query complete |
| `WARNING` | Missing optional data, fallbacks activated, deprecated usage |
| `ERROR` | Failed operations: query error, file not found, JSON parse failure |

---

## What to Log

- `INFO`: DB connection established, CSV file loaded, analysis complete
- `WARNING`: A row failed JSON parsing but processing continues
- `ERROR`: Query failed, file not found, missing required env variable

---

## What NOT to Log

- **NEVER** log DB passwords, connection strings, or API keys
- **NEVER** log raw user data that may contain PII
- Avoid logging entire DataFrames — log shape/size instead: `logger.info(f"Loaded {len(df)} rows")`

---

## Marimo UI Feedback (Preferred in Notebooks)

In Marimo notebooks, prefer visual callouts over print/logging for user-facing messages:

```python
mo.callout("✅ Conexión exitosa", kind="success")
mo.callout("⚠️ No se encontraron registros", kind="warn")
mo.callout("❌ Error al cargar archivo", kind="danger")
mo.md(f"Cargados **{len(df):,}** registros")
```

---

## Examples

- Logger setup: `marimo_lab/sentiance_analyzer_ia.py` (setup cell)
- UI feedback pattern: `csv_analizer/primary_scores.py` (DB connection cell)

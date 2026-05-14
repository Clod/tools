# Error Handling

> How errors are handled in this project.

---

## Overview

This is a Python data analytics project. Error handling focuses on:
- Per-row JSON decoding errors (not crashing entire pipeline)
- Missing environment variables
- Database connection failures
- File not found for CSV inputs

---

## JSON Decoding — Per-Row Pattern

When parsing JSON from SQL, catch errors per row and continue:

```python
import json

def parse_json_safe(raw_json: str) -> dict:
    try:
        return json.loads(raw_json)
    except (json.JSONDecodeError, TypeError) as e:
        return {"_parse_error": str(e), "_raw": raw_json}
```

This prevents a single bad row from failing the entire analysis.

---

## Missing Credentials

Check for missing env vars at setup time, not at query time:

```python
required_vars = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASS"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {missing}")
```

In Marimo notebooks, surface as a visual callout instead of raising:

```python
if not all([server, database, username, password]):
    engine = None
    db_status = mo.callout("Faltan credenciales en .env", kind="warn")
```

---

## File Not Found

Validate file paths before loading, with a clear message:

```python
from pathlib import Path

csv_path = Path(csv_dir) / "primary_safety_scores_transports.csv"
if not csv_path.exists():
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
```

In Marimo, surface as a `mo.callout(..., kind="danger")`.

---

## Database Query Errors

Wrap queries in try/except and show a meaningful message:

```python
try:
    df = pd.read_sql(query, engine)
except Exception as e:
    df = pd.DataFrame()
    mo.callout(f"Error ejecutando query: {e}", kind="danger")
```

---

## Anti-Patterns

- **NEVER** silently swallow exceptions: `except: pass`
- **NEVER** raise exceptions that print DB passwords or connection strings in the message
- **NEVER** let a single bad row kill the entire analysis pipeline

---

## Examples

- Per-row error handling: `marimo_lab/sentiance_data_explorer.py`
- Credential validation: `csv_analizer/primary_scores.py` (DB connection cell)

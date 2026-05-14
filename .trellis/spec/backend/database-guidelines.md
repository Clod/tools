# Database Guidelines

> Database patterns and conventions for SQL Server access in this project.

---

## Overview

The project connects to a **read-only SQL Server** instance. All DB access is for SELECT queries only. No INSERT, UPDATE, DELETE, ALTER, DROP, or CREATE is ever permitted.

---

## Connection Pattern

Always load credentials from `.env` (located at `marimo_lab/.env`). Never hardcode connection strings.

```python
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load .env from marimo_lab directory (adjust relative path as needed)
env_path = os.path.abspath(os.path.join(os.getcwd(), "../marimo_lab/.env"))
load_dotenv(env_path)

server   = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
port     = os.getenv("DB_PORT", "9433")

connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"
engine = create_engine(connection_string)
```

Required `.env` variables: `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_PORT`.

---

## Required Credential Validation

Always check credentials before attempting a connection and surface a clear warning in the UI:

```python
if all([server, database, username, password]):
    engine = create_engine(connection_string)
    db_status = mo.md(f"✅ Connected to `{database}` on `{server}`")
else:
    engine = None
    db_status = mo.callout("Faltan credenciales de base de datos en .env", kind="warn")
```

---

## Query Patterns

Use `pd.read_sql()` with the SQLAlchemy engine for all SELECT queries:

```python
import pandas as pd

df = pd.read_sql("SELECT TOP 100 * FROM SentianceEventos WHERE EventoTipo = 'transport'", engine)
```

---

## JSON Decoding from SQL

The `JSON` column in `MovDebug_Eventos` and `SentianceEventos` contains serialized JSON strings. **Do not** use SQL Server JSON functions. Instead:

1. Fetch the raw JSON string into a pandas DataFrame
2. Decode row-by-row with `json.loads()` inside a `try/except` per row

```python
import json

def parse_json_column(df, col="JSON"):
    results = []
    for idx, row in df.iterrows():
        try:
            results.append(json.loads(row[col]))
        except (json.JSONDecodeError, TypeError) as e:
            results.append({"error": str(e), "raw": row[col]})
    return results
```

Errors are reported per row, not as a full process failure.

---

## Key Tables

| Table | Description |
|-------|-------------|
| `SentianceEventos` | Raw SDK events with nested JSON column |
| `MovDebug_Eventos` | MovDebug event log with JSON column |
| `PuntajesPrirmariosTr` | Pre-processed primary safety scores per transport |
| `PuntajesSecundariosTr` | Pre-processed secondary safety scores per transport |
| `Conduccion` | Drive sessions/transports base table |

---

## Naming Conventions

- Table names: `PascalCase` (SQL Server convention in this project)
- Column names: mixed — follow existing schema in `Documentacion_Esquema_SQL_Actualizado.md`

---

## Anti-Patterns

- **NEVER** hardcode credentials: `engine = create_engine("mssql+pymssql://user:pass@...")`
- **NEVER** write to the database: no INSERT, UPDATE, DELETE, ALTER, DROP, CREATE
- **NEVER** use SQL Server JSON functions — always decode in Python/pandas
- **NEVER** load .env from a hard-coded absolute path that won't work on other machines

---

## Examples

- Full connection setup: `csv_analizer/primary_scores.py` cells 1-3
- JSON decoding pattern: `marimo_lab/sentiance_data_explorer.py`

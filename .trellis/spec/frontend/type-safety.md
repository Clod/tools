# Type Safety

> Type safety conventions in this Python project.

---

## Overview

This is a Python project. Type safety is handled via Python type hints (`typing` module). There is no TypeScript.

---

## Type Hints

Use type hints on all function signatures:

```python
from typing import Dict, List, Any, Optional
import pandas as pd

def parse_json_column(df: pd.DataFrame, col: str = "JSON") -> List[Dict[str, Any]]:
    ...

def build_connection_string(server: str, db: str, user: str, pwd: str, port: str = "9433") -> str:
    ...
```

---

## Optional Values

Use `Optional[T]` (or `T | None`) for values that may not be present:

```python
from typing import Optional

def get_engine(env_path: str) -> Optional[object]:
    load_dotenv(env_path)
    if not all([os.getenv("DB_SERVER"), os.getenv("DB_USER")]):
        return None
    return create_engine(...)
```

---

## DataFrame Typing

pandas DataFrames are typed as `pd.DataFrame`. Document expected columns in the docstring:

```python
def merge_scores(csv_df: pd.DataFrame, sql_df: pd.DataFrame) -> pd.DataFrame:
    """
    Args:
        csv_df: columns [transport_id, smooth_score, focus_score]
        sql_df: columns [transport_id, smooth_score_db, focus_score_db]
    Returns:
        Merged DataFrame with suffixed columns for disambiguation
    """
    return pd.merge(csv_df, sql_df, on="transport_id", suffixes=("_csv", "_db"))
```

---

## JSON Data Typing

JSON extracted from SQL is untyped at parse time. Use `Dict[str, Any]` and validate keys defensively:

```python
def extract_score(event: Dict[str, Any], key: str) -> Optional[float]:
    scores = event.get("safetyScores", {})
    value = scores.get(key)
    return float(value) if value is not None else None
```

---

## Anti-Patterns

- Avoid bare `except:` that hides type errors
- Avoid implicit type coercion: be explicit with `str()`, `float()`, `int()`
- Don't use mutable default arguments: `def f(lst=[]):` → use `def f(lst=None): if lst is None: lst = []`

---

## Examples

- Type hint usage: `marimo_lab/sentiance_analyzer.py` (LLM caller function)
- Optional pattern: `csv_analizer/primary_scores.py` (engine setup cell)

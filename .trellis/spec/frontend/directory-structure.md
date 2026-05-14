# Directory Structure

> How Marimo notebook UI code is organized in this project.

---

## Overview

This project uses **Marimo** as its UI/frontend framework. There is no React, TypeScript, or traditional web frontend. The "frontend" consists of Python files that define interactive Marimo notebooks.

---

## Directory Layout

```
tools/
├── marimo_lab/                      # Main interactive notebooks (primary UI layer)
│   ├── sentiance_data_explorer.py   # Main data explorer app
│   ├── sentiance_analyzer.py        # LLM-powered SDK analyzer app
│   ├── build_index.py               # Docs indexer notebook
│   ├── classify_concepts.py         # Concept classification notebook
│   └── pyproject.toml               # Dependencies for this module
│
├── csv_analizer/                    # Secondary analysis notebooks
│   ├── primary_scores.py            # Safety scores comparison app
│   └── movdebug_trips_extractor.py  # Trip data extractor notebook
│
└── visualizador_rutas/              # Geographic visualization tools
    ├── json_geo_gui.py              # Route visualization GUI
    └── waypoints_to_geojson.py      # Waypoints → GeoJSON converter
```

---

## Notebook Organization

Each Marimo notebook (`*.py`) is a self-contained application with:

1. **Module docstring** — explains purpose, inputs required, how to run
2. **`/// script` metadata block** — declares Python version and pip dependencies
3. **`import marimo` + `app = marimo.App()`** — always at top level
4. **Cells as `@app.cell` decorated functions** — each cell is a function

---

## Naming Conventions

- Notebook files: `snake_case.py` describing the purpose (e.g., `sentiance_data_explorer.py`)
- Cell functions: use descriptive names or `_()` for unnamed cells
- Variables: `snake_case` following Python convention

---

## New Notebook Location

- Exploratory/interactive tools for Sentiance data → `marimo_lab/`
- CSV/file-centric analysis → `csv_analizer/`
- Geographic data tools → `visualizador_rutas/`

---

## Examples

- Full-featured notebook: `marimo_lab/sentiance_data_explorer.py`
- Simpler analysis notebook: `csv_analizer/primary_scores.py`

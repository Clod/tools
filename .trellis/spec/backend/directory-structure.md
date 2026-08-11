# Directory Structure

> How backend/Python code is organized in this project.

---

## Overview

This is a Python data analytics project. "Backend" refers to Python data processing scripts, utility functions, and data extraction logic.

---

## Directory Layout

```
tools/
├── csv/                        # Input CSV files (pre-extracted from DB or SDK)
│   ├── primary_safety_scores_transports.csv
│   ├── secondary_safety_scores_transports.csv
│   ├── transports.csv
│   └── driving_events_*.csv
│
├── csv_analizer/               # Data analysis scripts and utilities
│   ├── primary_scores.py       # Marimo notebook: safety scores comparator
│   ├── movdebug_trips_extractor.py  # Trip data extractor
│   └── generate_report.py      # Standalone utility script (non-marimo)
│
├── marimo_lab/                 # Main interactive Marimo notebooks
│   ├── .env                    # DB credentials (gitignored, NEVER committed)
│   ├── sentiance_data_explorer.py   # Main data explorer notebook
│   ├── sentiance_analyzer_ia.py     # LLM-powered SDK analyzer
│   ├── build_index.py               # Docs indexer
│   ├── classify_concepts.py         # Concept classifier
│   ├── concepts.json                # Concept definitions
│   ├── SALIDA.json                  # Keywords index output
│   └── pyproject.toml               # uv project config
│
├── scraper/                    # Documentation scraping tools
│   ├── scraped_site/           # Local copy of Sentiance SDK docs (ground truth)
│   ├── crawler_sitemap.py      # Sitemap crawler
│   ├── crawler_tree.py         # Tree crawler
│   └── pyproject.toml
│
├── constantes/                 # Shared constants and reference data
│
├── visualizador_rutas/         # Route visualization tools (GeoJSON, leafmap)
│   ├── json_geo_gui.py         # GUI for route visualization
│   └── waypoints_to_geojson.py # Converts waypoints to GeoJSON
│
├── agents.md                   # AI agent instructions for this workspace
└── Documentacion_Esquema_SQL_Actualizado.md  # SQL schema documentation
```

---

## Module Organization

Each subdirectory is a self-contained project with its own `pyproject.toml` when it has dependencies. New data analysis tasks go in:

- `csv_analizer/` — if it primarily processes CSV files
- `marimo_lab/` — if it's an interactive Marimo notebook for exploration
- A new subdirectory — for completely standalone tools

---

## Naming Conventions

- Python files: `snake_case.py`
- Marimo notebooks: descriptive `snake_case.py` (they are Python files)
- JSON data outputs: `UPPERCASE.json` for index files, `lowercase.json` for data
- CSV files: `descriptive_name.csv`
- Directories: `snake_case/`

---

## Examples

- Well-organized Marimo notebook: `csv_analizer/primary_scores.py`
- Standalone utility script: `csv_analizer/generate_report.py`
- Data explorer with full layout: `marimo_lab/sentiance_data_explorer.py`

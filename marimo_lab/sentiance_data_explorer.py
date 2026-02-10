"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SENTIANCE DATA EXPLORER - MARIMO NOTEBOOK                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ WHAT THIS NOTEBOOK DOES:                                                     ║
║ - Connects to SQL Server database to query Sentiance event data              ║
║ - Provides filtering by Sentiance ID and date/time range                     ║
║ - Displays results in an interactive table with row selection                ║
║ - Shows detailed JSON field viewer for selected rows                         ║
║ - Extracts and visualizes geographic data (venues/paths) on an interactive   ║
║   map using leafmap                                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ HOW TO RUN THIS NOTEBOOK:                                                    ║
║                                                                              ║
║ 1. EDIT MODE (Recommended for development):                                  ║
║    $ marimo edit app.py                                                      ║
║    Opens in browser with full IDE: code cells, output, and ability to modify ║
║                                                                              ║
║ 2. RUN MODE (Read-only app view):                                            ║
║    $ marimo run app.py                                                       ║
║    Opens as a clean app - users see outputs & UI widgets only, no code       ║
║                                                                              ║
║ 3. CONVERT TO HTML (Static export):                                          ║
║    $ marimo export html app.py -o app.html                                   ║
║    Creates a static HTML file (no interactivity, just a snapshot)            ║
║                                                                              ║
║ 4. AS PYTHON SCRIPT (No UI):                                                 ║
║    $ python app.py                                                           ║
║    Runs cells in order but without the web interface                         ║
║                                                                              ║
║ 5. CONVERT TO JUPYTER (Migration):                                           ║
║    $ marimo export ipynb app.py -o app.ipynb                                 ║
║    Converts to Jupyter notebook format                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# =============================================================================
# MARIMO IMPORT & APP INITIALIZATION
# =============================================================================
# Every marimo notebook MUST start with this import. It's the core library.
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "sqlalchemy",
#     "pymssql",
#     "leafmap",
#     "python-dotenv",
# ]
# ///

import marimo

# __generated_with tracks which marimo version created this file.
# Marimo uses this for compatibility checks. Don't modify manually.
__generated_with = "0.19.2"

# =============================================================================
# APP OBJECT CREATION
# =============================================================================
# marimo.App() creates the application instance. This is the container for all cells.
#
# CONFIGURATION OPTIONS:
#   width="full"     - Uses full browser width (default is "medium" ~1200px)
#   width="medium"   - Fixed medium width, centered
#   width="compact"  - Narrower layout for reading
#
# Other App() options include:
#   css_file="style.css"  - Custom CSS styling
#   layout_file="layout.json" - Custom cell layout
app = marimo.App(width="full")


# =============================================================================
# CELL 1: IMPORTS & ENVIRONMENT SETUP
# =============================================================================
# @app.cell is the DECORATOR that defines a marimo cell.
#
# DECORATOR OPTIONS:
#   hide_code=True  - Hides the code in "run" mode (users only see output)
#   disabled=True   - Cell won't execute (useful for debugging)
#
# CRITICAL MARIMO CONCEPT - REACTIVITY:
# Marimo automatically tracks dependencies between cells based on:
#   1. Variables RETURNED by a cell (in the return statement)
#   2. Variables USED by other cells (in their function parameters)
#
# When a cell's returned value changes, ALL cells that depend on it 
# automatically re-execute. This is marimo's "reactive" programming model.
@app.cell(hide_code=True)
def _():
    # ==========================================================================
    # IMPORTS INSIDE CELLS
    # ==========================================================================
    # In marimo, imports are typically done inside cells and RETURNED.
    # This makes them available to other cells that need them.
    # 
    # WHY? Because marimo tracks dependencies through the return statement.
    # If you import at the top level (outside cells), marimo can't track it.
    
    import marimo as mo  # 'mo' is the conventional alias for marimo
    import pandas as pd
    import json
    import sqlalchemy
    import leafmap
    import os
    from dotenv import load_dotenv

    load_dotenv()
    
    # ==========================================================================
    # RETURN STATEMENT - THE HEART OF MARIMO REACTIVITY
    # ==========================================================================
    # EVERYTHING a cell wants to "export" to other cells MUST be returned.
    # 
    # Return formats:
    #   return (var1, var2, var3)  - Tuple: exports multiple variables
    #   return (single_var,)       - Single variable (note the trailing comma!)
    #   return                     - Nothing exported (cell is a "sink")
    #
    # The returned variables become available as PARAMETERS to other cells.
    return json, leafmap, mo, os, pd, sqlalchemy


# =============================================================================
# CELL 2: MARKDOWN HEADER
# =============================================================================
# Notice how this cell has 'mo' in its parameters - this means it DEPENDS on
# the previous cell that returned 'mo'. Marimo ensures this cell runs AFTER
# the cell that provides 'mo'.
@app.cell(hide_code=True)
def _(mo):
    # ==========================================================================
    # mo.md() - MARKDOWN RENDERING
    # ==========================================================================
    # mo.md() converts markdown text to formatted HTML output.
    # 
    # IMPORTANT: The LAST expression in a cell is automatically displayed.
    # You don't need print() - just put the expression as the last line.
    #
    # Supports full markdown: headers, bold, italic, code blocks, tables, etc.
    # Also supports emoji directly in the text! 🎉
    mo.md("""
    # Welcome to Marimo! 🌊
    """)
    return  # Empty return = this cell exports nothing


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### SQL Server Connection
    To connect to your SQL Server, we'll use `sqlalchemy` and `pymssql`.
    You can use the cell below to define your connection string.
    """)
    return


# =============================================================================
# CELL 4: DATABASE ENGINE CREATION
# =============================================================================
@app.cell(hide_code=True)
def _(os, sqlalchemy):
    # Database credentials from environment variables
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    port = os.getenv("DB_PORT", 9433)

    connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"
    engine = sqlalchemy.create_engine(connection_string)
    
    # ==========================================================================
    # SINGLE VARIABLE RETURN SYNTAX
    # ==========================================================================
    # When returning a single variable, you MUST use a trailing comma: (var,)
    # This tells Python it's a tuple, not just parentheses for grouping.
    # Without the comma: (engine) is just 'engine' with parentheses
    # With the comma: (engine,) is a tuple containing 'engine'
    return (engine,)


# =============================================================================
# CELL 5: TABLE SELECTOR DROPDOWN
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("### Table Selection")
    
    # ==========================================================================
    # mo.ui - MARIMO'S UI COMPONENTS
    # ==========================================================================
    # mo.ui contains all interactive widgets. They are REACTIVE - when user
    # interacts with them, any cell depending on that widget re-executes!
    #
    # mo.ui.dropdown() - Creates a dropdown/select menu
    # PARAMETERS:
    #   options: list of strings OR dict {label: value}
    #   value: initial selected value
    #   label: text label shown above the dropdown
    #
    # ACCESSING THE VALUE:
    #   widget.value - returns the currently selected value
    #   This value updates automatically when user makes a selection!
    table_selector = mo.ui.dropdown(
        options=["SentianceEventos", "MovDebug_Eventos"],
        value="MovDebug_Eventos",
        label="Select Source Table"
    )
    
    # ==========================================================================
    # DISPLAYING UI ELEMENTS
    # ==========================================================================
    # Just reference the widget as the last expression to display it.
    # It will render as an interactive dropdown in the output.
    table_selector
    return (table_selector,)


# =============================================================================
# CELL 6: FILTER INPUT CONTROLS
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("### Data Filtering")
    
    # ==========================================================================
    # MORE UI COMPONENTS
    # ==========================================================================
    # mo.ui.text() - Single line text input
    #   label: label text
    #   placeholder: gray hint text shown when empty
    #   value: initial value (optional)
    sid_input = mo.ui.text(label="Sentiance ID", placeholder="Enter ID...")
    
    # mo.ui.datetime() - Date and time picker
    #   label: label text
    #   value: initial datetime (optional)
    # start_dt = mo.ui.datetime(label="Start Date/Time")
    # end_dt = mo.ui.datetime(label="End Date/Time")
    import datetime
    start_dt = mo.ui.datetime(label="Start Date/Time", value=datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
    end_dt = mo.ui.datetime(label="End Date/Time", value=datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0))


    # ==========================================================================
    # mo.hstack() / mo.vstack() - LAYOUT COMPONENTS
    # ==========================================================================
    # mo.hstack() - Arranges elements HORIZONTALLY (side by side)
    # mo.vstack() - Arranges elements VERTICALLY (stacked)
    #
    # PARAMETERS:
    #   items: list of elements to arrange
    #   gap: spacing between items (in rem units, ~16px)
    #   align: "start", "center", "end", "stretch"
    #   justify: "start", "center", "end", "space-between", "space-around"
    filter_ui = mo.hstack([sid_input, start_dt, end_dt], gap=2)
    filter_ui
    return end_dt, sid_input, start_dt


# =============================================================================
# CELL 7: SQL QUERY EXECUTION
# =============================================================================
# This cell depends on MANY upstream values - notice they're all in the params!
# Marimo will re-run this cell whenever ANY of these change:
#   - end_dt, start_dt, sid_input (when user changes filter inputs)
#   - table_selector (when user picks different table)
#   - engine, mo (from initialization)
@app.cell(hide_code=True)
def _(end_dt, engine, mo, sid_input, start_dt, table_selector):
    # Build dynamic SQL query
    base_query = f"SELECT TOP 100 * FROM VictaTMTK.dbo.{table_selector.value}"
    where_clauses = []

    # .value is how you access the current value of ANY mo.ui widget
    sid = sid_input.value.strip() if sid_input.value else None
    start = start_dt.value if start_dt.value else None
    end = end_dt.value if end_dt.value else None

    if sid:
        where_clauses.append(f"sentianceid = '{sid}'")
    if start:
        where_clauses.append(f"fechahora >= '{start}'")
    if end:
        where_clauses.append(f"fechahora <= '{end}'")

    query = base_query
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY fechahora DESC"

    # ==========================================================================
    # mo.accordion() - COLLAPSIBLE SECTIONS
    # ==========================================================================
    # Creates expandable/collapsible sections. Great for optional details.
    # Takes a dict: {title: content}
    # Multiple items create multiple collapsible sections.
    query_log = mo.accordion({
        "📝 SQL Query Log": mo.md(f"```sql\n{query}\n```")
    })

    # ==========================================================================
    # mo.sql() - BUILT-IN SQL EXECUTION
    # ==========================================================================
    # Marimo has native SQL support! mo.sql() executes queries and returns DataFrame.
    #
    # PARAMETERS:
    #   query: SQL string to execute
    #   output: if True, displays result table automatically; False = just return data
    #   engine: SQLAlchemy engine for the database connection
    #
    # Returns a pandas DataFrame with the query results.
    df = mo.sql(
        query,
        output=False,  # We'll display in our own table widget
        engine=engine
    )

    query_log  # Display the accordion
    return (df,)  # Export the DataFrame for other cells


# =============================================================================
# CELL 8: INTERACTIVE DATA TABLE
# =============================================================================
@app.cell(hide_code=True)
def _(df, mo):
    # ==========================================================================
    # mo.ui.table() - INTERACTIVE DATA TABLE
    # ==========================================================================
    # Renders a DataFrame as an interactive, sortable, filterable table.
    #
    # PARAMETERS:
    #   data: DataFrame or list of dicts
    #   selection: "single" | "multi" | None
    #       - "single": user can select one row
    #       - "multi": user can select multiple rows  
    #       - None: no selection allowed
    #   label: description text
    #   page_size: rows per page (default 10)
    #   pagination: True/False to enable paging
    #
    # REACTIVE SELECTION:
    #   table.value returns a DataFrame of selected row(s)
    #   When selection changes, cells using table.value re-execute!
    table = mo.ui.table(df, selection="single", label="Select a row to see details")
    table
    return (table,)


# =============================================================================
# CELL 9: ROW DETAIL VIEWER
# =============================================================================
# This cell reacts to table selection - when user clicks a row, this updates!
@app.cell(hide_code=True)
def _(json, mo, table):
    # table.value is a DataFrame of selected rows (empty if nothing selected)
    selected_row = table.value

    if len(selected_row) > 0:
        row_data = selected_row.iloc[0]
        left_items = []
        right_items = []

        for col in row_data.index:
            val = row_data[col]
            formatted_val = str(val)
            is_json = False

            try:
                if isinstance(val, str) and val.strip().startswith(("{", "[")):
                    parsed = json.loads(val)
                    formatted_val = json.dumps(parsed, indent=4)
                    is_json = True
                elif isinstance(val, (dict, list)):
                    formatted_val = json.dumps(val, indent=4)
                    is_json = True
            except:
                pass

            box_height = 25 if is_json else 2

            # =================================================================
            # mo.ui.text_area() - MULTI-LINE TEXT INPUT
            # =================================================================
            # Like text() but for multi-line content. 
            #   disabled=True makes it read-only (display only)
            #   rows: number of visible text rows
            field_ui = mo.vstack([
                mo.md(f"**{col}**"),
                mo.ui.text_area(value=formatted_val, disabled=True, rows=box_height)
            ], gap=0.5)

            if is_json or "json" in col.lower():
                right_items.append(field_ui)
            else:
                left_items.append(field_ui)

        # Nested layout: vstack inside hstack for complex layouts
        view = mo.vstack([
            mo.md("### Row Detail"),
            mo.hstack([
                mo.vstack(left_items, gap=1, align="stretch"),
                mo.vstack(right_items, gap=1, align="stretch")
            ], gap=2, align="start")
        ], gap=1)
    else:
        view = mo.md("💡 *Select a row in the table above to view its details here.*")

    view  # Display the constructed view
    return  # No exports - this is a display-only cell


# =============================================================================
# CELL 10: GEOGRAPHIC DATA EXTRACTION
# =============================================================================
@app.cell(hide_code=True)
def _(json, mo, pd, table):
    geo_selected_row = table.value

    if len(geo_selected_row) > 0:
        geo_row_data = geo_selected_row.iloc[0]
        geo_data_found = []

        def find_geo_structures(obj, parent_key="", in_path=False):
            """Recursively find waypoints or lat/long in dicts/lists"""
            if isinstance(obj, dict):
                current_is_path = False
                g_type = obj.get("type", obj.get("venue_type"))
                g_significance = obj.get("significance")
                g_accuracy = obj.get("accuracy")

                if "waypoints" in obj:
                    geo_data_found.append({
                        "Source": parent_key or "root",
                        "Kind": "Path 🛤️",
                        "GeoType": g_type,
                        "Significance": g_significance,
                        "Accuracy": g_accuracy,
                        "Summary": f"{len(obj['waypoints'])} waypoints found",
                        "Data": obj
                    })
                    current_is_path = True
                else:
                    coords = None
                    if "latitude" in obj and "longitude" in obj:
                        coords = (obj["latitude"], obj["longitude"])
                    elif isinstance(obj.get("location"), dict) and "latitude" in obj["location"] and "longitude" in obj["location"]:
                        coords = (obj["location"]["latitude"], obj["location"]["longitude"])
                        g_accuracy = g_accuracy or obj["location"].get("accuracy")

                    if coords and not in_path:
                        geo_data_found.append({
                            "Source": parent_key or "root",
                            "Kind": "Venue 📍",
                            "GeoType": g_type,
                            "Significance": g_significance,
                            "Accuracy": g_accuracy,
                            "Summary": f"Coord: {coords[0]}, {coords[1]}",
                            "Data": obj,
                            "Lat": coords[0],
                            "Lon": coords[1]
                        })

                for k, v in obj.items():
                    find_geo_structures(v, f"{parent_key}.{k}" if parent_key else k, in_path=in_path or current_is_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_geo_structures(item, f"{parent_key}[{i}]", in_path=in_path)

        for geo_col in geo_row_data.index:
            geo_val = geo_row_data[geo_col]
            if isinstance(geo_val, str) and geo_val.strip().startswith(("{", "[")):
                try:
                    geo_parsed = json.loads(geo_val)
                    find_geo_structures(geo_parsed, geo_col)
                except:
                    pass
            elif isinstance(geo_val, (dict, list)):
                find_geo_structures(geo_val, geo_col)

        if geo_data_found:
            geo_df = pd.DataFrame(geo_data_found)
            table_cols = ["Kind", "Source", "GeoType", "Significance", "Accuracy", "Summary"]
            table_cols = [c for c in table_cols if c in geo_df.columns]
            geo_table_ui = mo.ui.table(geo_df[table_cols], selection="single", label="Select to zoom in map")
        else:
            geo_table_ui = None
            geo_df = None
            geo_data_found = []
    else:
        geo_table_ui = None
        geo_df = None
        geo_data_found = []
    return geo_data_found, geo_df, geo_table_ui


# =============================================================================
# CELL 11: MAP VISUALIZATION
# =============================================================================
# This cell demonstrates a complex reactive chain:
# 1. Depends on geo_table_ui from previous cell
# 2. When user selects row in geo_table_ui, this cell re-runs
# 3. Map updates to show just the selected element
@app.cell(hide_code=True)
def _(geo_data_found, geo_df, geo_table_ui, json, leafmap, mo):
    if geo_table_ui is not None and geo_df is not None:
        if len(geo_table_ui.value) > 0:
            selected_item = geo_table_ui.value.iloc[0]
            orig_item = geo_df[geo_df["Source"] == selected_item["Source"]].iloc[0]

            if orig_item["Kind"] == "Venue 📍":
                m = leafmap.Map(backend="ipyleaflet", center=[orig_item["Lat"], orig_item["Lon"]], zoom=15, minimize_control=True)
                m.add_marker(location=[orig_item["Lat"], orig_item["Lon"]], tooltip=f"{orig_item['Source']} - SELECTED")
            elif orig_item["Kind"] == "Path 🛤️":
                pts = [[p["latitude"], p["longitude"]] for p in orig_item["Data"]["waypoints"]]
                if pts:
                    center_lat = sum(p[0] for p in pts) / len(pts)
                    center_lon = sum(p[1] for p in pts) / len(pts)
                    m = leafmap.Map(backend="ipyleaflet", center=[center_lat, center_lon], zoom=13, minimize_control=True)
                    coords = [[p["longitude"], p["latitude"]] for p in orig_item["Data"]["waypoints"]]
                    line_geojson = {
                        "type": "FeatureCollection",
                        "features": [{
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": coords},
                            "properties": {"name": f"{orig_item['Source']} - SELECTED"}
                        }]
                    }
                    m.add_geojson(line_geojson, layer_name=orig_item["Source"])
                else:
                    m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
            else:
                m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
        else:
            m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
            for idx, row in geo_df.iterrows():
                if row["Kind"] == "Venue 📍":
                    m.add_marker(location=[row["Lat"], row["Lon"]], tooltip=f"{row['Source']} ({row['GeoType'] or ''})")
                elif row["Kind"] == "Path 🛤️":
                    coords = [[p["longitude"], p["latitude"]] for p in row["Data"]["waypoints"]]
                    if coords:
                        line_geojson = {
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": {"type": "LineString", "coordinates": coords},
                                "properties": {"name": row["Source"]}
                            }]
                        }
                        m.add_geojson(line_geojson, layer_name=row["Source"])

        geo_view = mo.vstack([
            mo.md("## 🌍 Interactive Geographic View"),
            mo.hstack([
                mo.vstack([mo.md("### Elements"), geo_table_ui], align="stretch"),
                mo.vstack([mo.md("### Map"), m], align="stretch")
            ], gap=2, align="start"),
            mo.md("### Details"),
            mo.vstack([
                mo.vstack([
                    mo.md(f"#### {item['Kind']} (from `{item['Source']}`)"),
                    mo.md(f"**Description:** {item['Summary']}"),
                    mo.accordion({"Raw Data": mo.ui.text_area(value=json.dumps(item['Data'], indent=2), disabled=True, rows=10)})
                ], gap=0.5) for item in geo_data_found
            ], gap=2)
        ])
    else:
        geo_view = mo.md("ℹ️ *No geographic information detected.*")

    geo_view
    return


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# This allows running the notebook as a Python script: python app.py
# When run this way, cells execute in dependency order without the UI.
if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import json
    import sqlalchemy
    import leafmap
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()
    return json, leafmap, mo, os, pd, sqlalchemy


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Welcome to Marimo! 🌊
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### SQL Server Connection
    To connect to your SQL Server, we'll use `sqlalchemy` and `pymssql`.
    You can use the cell below to define your connection string.
    """)
    return


@app.cell(hide_code=True)
def _(os, sqlalchemy):
    # Credentials are now loaded from the .env file for security
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    port = os.getenv("DB_PORT", 9433)

    # Connection string for pymssql
    connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"

    # Create engine
    engine = sqlalchemy.create_engine(connection_string)
    return (engine,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Table Selection")
    table_selector = mo.ui.dropdown(
        options=["SentianceEventos", "MovDebug_Eventos"],
        value="SentianceEventos",
        label="Select Source Table"
    )
    table_selector
    return (table_selector,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Data Filtering")
    sid_input = mo.ui.text(label="Sentiance ID", placeholder="Enter ID...")
    start_dt = mo.ui.datetime(label="Start Date/Time")
    end_dt = mo.ui.datetime(label="End Date/Time")

    filter_ui = mo.hstack([sid_input, start_dt, end_dt], gap=2)
    filter_ui
    return end_dt, sid_input, start_dt


@app.cell(hide_code=True)
def _(end_dt, engine, mo, sid_input, start_dt, table_selector):
    # Prepare the query with filters
    base_query = f"SELECT TOP 100 * FROM VictaTMTK.dbo.{table_selector.value}"
    where_clauses = []

    # Clean up and validate inputs
    sid = sid_input.value.strip() if sid_input.value else None
    start = start_dt.value if start_dt.value else None
    end = end_dt.value if end_dt.value else None

    if sid:
        where_clauses.append(f"sentianceid = '{sid}'")

    if start:
        # standard ISO format works best with SQL Server
        where_clauses.append(f"fechahora >= '{start}'")

    if end:
        where_clauses.append(f"fechahora <= '{end}'")

    query = base_query
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    # Sorting by fechahora to see the most recent or chronological data
    query += " ORDER BY fechahora DESC"

    # Logging the query for debugging
    query_log = mo.accordion({
        "📝 SQL Query Log": mo.md(f"```sql\n{query}\n```")
    })

    df = mo.sql(
        query,
        output=False,
        engine=engine
    )

    # Display the log
    query_log
    return (df,)


@app.cell(hide_code=True)
def _(df, mo):
    # Display the interactive table with single-row selection
    table = mo.ui.table(df, selection="single", label="Select a row to see details")
    table
    return (table,)


@app.cell(hide_code=True)
def _(json, mo, table):
    # Check if a row is selected
    selected_row = table.value

    if len(selected_row) > 0:
        # Get the first (and only) selected row
        row_data = selected_row.iloc[0]

        # Lists to hold the UI components for each column
        left_items = []
        right_items = []

        for col in row_data.index:
            val = row_data[col]

            # Attempt to format as JSON if it's potentially a JSON object
            formatted_val = str(val)
            is_json = False

            try:
                # If it looks like JSON (starts with { or [)
                if isinstance(val, str) and val.strip().startswith(("{", "[")):
                    parsed = json.loads(val)
                    formatted_val = json.dumps(parsed, indent=4)
                    is_json = True
                elif isinstance(val, (dict, list)):
                    formatted_val = json.dumps(val, indent=4)
                    is_json = True
            except:
                pass

            # Create the UI component
            # Adaptive height: much taller for JSON fields
            box_height = 25 if is_json else 2

            field_ui = mo.vstack([
                mo.md(f"**{col}**"),
                mo.ui.text_area(value=formatted_val, disabled=True, rows=box_height)
            ], gap=0.5)

            # Categorize: JSON on the right, everything else on the left
            if is_json or "json" in col.lower():
                right_items.append(field_ui)
            else:
                left_items.append(field_ui)

        # Assemble the final view
        view = mo.vstack([
            mo.md("### Row Detail"),
            mo.hstack([
                mo.vstack(left_items, gap=1, align="stretch"),
                mo.vstack(right_items, gap=1, align="stretch")
            ], gap=2, align="start")
        ], gap=1)
    else:
        view = mo.md("💡 *Select a row in the table above to view its details here.*")

    view
    return


@app.cell(hide_code=True)
def _(json, mo, pd, table):
    # Check if a row is selected
    geo_selected_row = table.value

    if len(geo_selected_row) > 0:
        geo_row_data = geo_selected_row.iloc[0]
        geo_data_found = []

        def find_geo_structures(obj, parent_key="", in_path=False):
            """Recursively find waypoints or lat/long in dicts/lists"""
            if isinstance(obj, dict):
                current_is_path = False

                # Metadata detection
                g_type = obj.get("type", obj.get("venue_type"))
                g_significance = obj.get("significance")
                g_accuracy = obj.get("accuracy")

                # 1. Check for Path (waypoints)
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

                # 2. Check for Venue / Location structure
                else:
                    coords = None
                    # Direct lat/long
                    if "latitude" in obj and "longitude" in obj:
                        coords = (obj["latitude"], obj["longitude"])
                    # Nested in 'location' (common in Sentiance data)
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

                # Continue searching sub-objects
                for k, v in obj.items():
                    find_geo_structures(v, f"{parent_key}.{k}" if parent_key else k, in_path=in_path or current_is_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_geo_structures(item, f"{parent_key}[{i}]", in_path=in_path)

        # Scan all columns in the row
        for geo_col in geo_row_data.index:
            geo_val = geo_row_data[geo_col]
            # Try to parse as JSON if it's a string
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

            # Interactive sub-table for selecting geo elements
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


@app.cell(hide_code=True)
def _(geo_data_found, geo_df, geo_table_ui, json, leafmap, mo):
    # This cell creates the map dynamically based on selection
    if geo_table_ui is not None and geo_df is not None:
        # Check if a specific element is selected
        if len(geo_table_ui.value) > 0:
            selected_item = geo_table_ui.value.iloc[0]
            orig_item = geo_df[geo_df["Source"] == selected_item["Source"]].iloc[0]

            # Create map focused on selected item
            if orig_item["Kind"] == "Venue 📍":
                m = leafmap.Map(backend="ipyleaflet", center=[orig_item["Lat"], orig_item["Lon"]], zoom=15, minimize_control=True)
                m.add_marker(location=[orig_item["Lat"], orig_item["Lon"]], tooltip=f"{orig_item['Source']} - SELECTED")
            elif orig_item["Kind"] == "Path 🛤️":
                pts = [[p["latitude"], p["longitude"]] for p in orig_item["Data"]["waypoints"]]
                if pts:
                    # Calculate center
                    center_lat = sum(p[0] for p in pts) / len(pts)
                    center_lon = sum(p[1] for p in pts) / len(pts)
                    m = leafmap.Map(backend="ipyleaflet", center=[center_lat, center_lon], zoom=13, minimize_control=True)

                    coords = [[p["longitude"], p["latitude"]] for p in orig_item["Data"]["waypoints"]]
                    line_geojson = {
                        "type": "FeatureCollection",
                        "features": [{
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords
                            },
                            "properties": {"name": f"{orig_item['Source']} - SELECTED"}
                        }]
                    }
                    m.add_geojson(line_geojson, layer_name=orig_item["Source"])
                else:
                    m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
            else:
                m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
        else:
            # No selection - show all elements
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
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": coords
                                },
                                "properties": {"name": row["Source"]}
                            }]
                        }
                        m.add_geojson(line_geojson, layer_name=row["Source"])

        # Layout: Table on left, Map on right
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


if __name__ == "__main__":
    app.run()

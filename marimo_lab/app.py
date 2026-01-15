import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import json
    import sqlalchemy
    return json, mo, pd, sqlalchemy


@app.cell
def _(mo):
    mo.md("""
    # Welcome to Marimo! 🌊
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### SQL Server Connection
    To connect to your SQL Server, we'll use `sqlalchemy` and `pymssql`.
    You can use the cell below to define your connection string.
    """)
    return


@app.cell
def _(sqlalchemy):
    # Update these with your actual credentials
    server = 'ltkbase003.cjo9vciowl0y.us-east-1.rds.amazonaws.com'
    database = 'VictaTMTK'
    username = 'ClaudioVicta'
    password = 'CV2026$'
    port = 9433

    # Connection string for pymssql
    # Format: mssql+pymssql://<username>:<password>@<server>:<port>/<database>
    connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"

    # Create engine (we don't connect yet to avoid errors if credentials are wrong)
    engine = sqlalchemy.create_engine(connection_string)
    return (engine,)


@app.cell
def _(engine, mo):
    # Execute the query and store result in a DataFrame
    df = mo.sql(
        f"""
        SELECT TOP 100 * FROM VictaTMTK.dbo.SentianceEventos
        """,
        output=False,
        engine=engine
    )
    return (df,)


@app.cell
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
                            "Data": obj
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

            # Display a nice table with the new metadata
            table_cols = ["Kind", "Source", "GeoType", "Significance", "Accuracy", "Summary"]
            # Ensure columns exist in df before selecting
            table_cols = [c for c in table_cols if c in geo_df.columns]

            # Create a display for each geo structure
            geo_displays = []
            for item in geo_data_found:
                metadata_lines = []
                if item.get("GeoType"): metadata_lines.append(f"**Type:** {item['GeoType']}")
                if item.get("Significance"): metadata_lines.append(f"**Significance:** {item['Significance']}")
                if item.get("Accuracy"): metadata_lines.append(f"**Accuracy:** {item['Accuracy']}m")

                geo_displays.append(
                    mo.vstack([
                        mo.md(f"#### {item['Kind']} (from `{item['Source']}`)"),
                        mo.md("  \n".join(metadata_lines)) if metadata_lines else mo.md(""),
                        mo.md(f"**Summary:** {item['Summary']}"),
                        mo.accordion({"Raw Data": mo.ui.text_area(value=json.dumps(item['Data'], indent=2), disabled=True, rows=10)})
                    ], gap=0.5)
                )

            geo_view = mo.vstack([
                mo.md("## 🌍 Geographic Information"),
                mo.ui.table(geo_df[table_cols], label="Detected Geographic Elements"),
                mo.md("### Details"),
                mo.vstack(geo_displays, gap=2)
            ])
        else:
            geo_view = mo.md("ℹ️ *No geographic information (waypoints/coordinates) detected in this record.*")
    else:
        geo_view = mo.md("")

    geo_view
    return


if __name__ == "__main__":
    app.run()

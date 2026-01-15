import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


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
def _():
    import sqlalchemy
    import pandas as pd

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
        engine=engine
    )
    return (df,)


@app.cell
def _(df, mo):
    # Display the interactive table with single-row selection
    table = mo.ui.table(df, selection="single", label="Select a row to see details")
    table
    return (table,)


@app.cell
def _(mo, table):
    import json

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


if __name__ == "__main__":
    app.run()

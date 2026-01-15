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
        SELECT TOP 10 * FROM VictaTMTK.dbo.SentianceEventos
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
        
        # We can map the columns to UI elements dynamically or specifically
        # Let's show the first 6 columns as requested
        cols = row_data.index[:6]
        
        items = []
        for col in cols:
            val = row_data[col]
            
            # Attempt to format as JSON if it's a string or a dict/list
            formatted_val = str(val)
            try:
                if isinstance(val, str):
                    # Try to parse string as JSON
                    parsed = json.loads(val)
                    formatted_val = json.dumps(parsed, indent=4)
                elif isinstance(val, (dict, list)):
                    # Already an object
                    formatted_val = json.dumps(val, indent=4)
            except:
                # Fallback to original string if not valid JSON
                pass
                
            items.append(
                mo.vstack([
                    mo.md(f"**{col}**"),
                    mo.ui.text_area(value=formatted_val, disabled=True, rows=10 if "json" in col.lower() or len(formatted_val) > 50 else 3)
                ])
            )
        
        view = mo.vstack([
            mo.md("### Row Detail"),
            mo.hstack([
                mo.vstack(items[0:3], gap=1),
                mo.vstack(items[3:6], gap=1)
            ], align="start", gap=2)
        ])
    else:
        view = mo.md("💡 *Select a row in the table above to view its details here.*")
        
    view
    return cols, items, json, row_data, selected_row, view


if __name__ == "__main__":
    app.run()

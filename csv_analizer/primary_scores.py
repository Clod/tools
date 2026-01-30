import marimo

__generated_with = "0.19.6"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import os
    import json
    import sqlalchemy
    from sqlalchemy import create_engine
    from dotenv import load_dotenv

    # Load .env from marimo_lab directory
    # Current notebook: tools/csv_analizer/primary_scores.py
    # .env: tools/marimo_lab/.env
    env_path = os.path.abspath(os.path.join(os.getcwd(), "../marimo_lab/.env"))
    load_dotenv(env_path)

    return create_engine, json, mo, os, pd


@app.cell
def _(mo):
    mo.md(r"""
    # Primary Safety Scores Analyzer
    This notebook displays the contents of `primary_safety_scores_transports.csv` and retrieves corresponding scores from the database for comparison.
    """)
    return


@app.cell
def _(create_engine, mo, os):
    # Database credentials from environment variables
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    port = os.getenv("DB_PORT", "9433")

    if all([server, database, username, password]):
        connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"
        engine = create_engine(connection_string)
        db_status = mo.md(f"✅ Connected to `{database}` on `{server}`")
    else:
        engine = None
        db_status = mo.callout("Database credentials missing in .env", kind="warn")

    return db_status, engine


@app.cell
def _(mo, pd):
    csv_path = "../csv/primary_safety_scores_transports.csv"

    df = None
    table = None
    stats_table = None

    if pd.io.common.file_exists(csv_path):
        df = pd.read_csv(csv_path)
        table = mo.ui.table(df, label="Safety Scores Grid (from CSV)", selection=None, pagination=True)

        # Summary stats
        stats = df.describe().reset_index()
        stats_table = mo.ui.table(stats, label="Summary Statistics")
    else:
        table = mo.callout(f"File not found: {csv_path}", kind="danger")

    return df, stats_table, table


@app.cell
def _(db_status, mo, stats_table, table):
    mo.vstack([
        db_status,
        mo.md("## Safety Scores Grid (from CSV)"),
        table,
        mo.md("## Summary Statistics"),
        stats_table
    ]) if table is not None else None
    return


@app.cell
def _(df, engine, json, mo, pd):
    db_df = None
    db_table = None

    if df is not None and engine is not None:
        db_scores = []

        # Extract scores for each row
        for index, row in df.iterrows():
            user_id = row['user_id']
            transport_id = row['transport_id']

            # SQL query using %like% for transport_id in the JSON field
            query = f"""
            SELECT TOP 1 JSON 
            FROM SentianceEventos 
            WHERE sentianceid = '{user_id}' 
            AND JSON LIKE '%{transport_id}%'
            """

            try:
                res_df = mo.sql(query, engine=engine, output=False)

                if not res_df.empty:
                    raw_json = res_df.iloc[0]['JSON']
                    data = json.loads(raw_json)

                    # Extract safety scores from the JSON structure
                    scores = data.get("safetyScores", {})

                    db_scores.append({
                        "user_id": user_id,
                        "transport_id": transport_id,
                        "legal": scores.get("legalScore", "N/A"),
                        "smooth": scores.get("smoothScore", "N/A"),
                        "attention": scores.get("focusScore", "N/A"), # Mapping focusScore to attention
                        "overall": scores.get("overallScore", "N/A"),
                        "harsh_accel": scores.get("harshAccelerationScore", "N/A"),
                        "harsh_brake": scores.get("harshBrakingScore", "N/A"),
                        "harsh_turn": scores.get("harshTurningScore", "N/A"),
                        "call_moving": scores.get("callWhileMovingScore", "N/A")
                    })
                else:
                    db_scores.append({
                        "user_id": user_id,
                        "transport_id": transport_id,
                        "legal": "N/A", "smooth": "N/A", "attention": "N/A", "overall": "N/A",
                        "harsh_accel": "N/A", "harsh_brake": "N/A", "harsh_turn": "N/A", "call_moving": "N/A"
                    })
            except Exception as e:
                db_scores.append({
                    "user_id": user_id,
                    "transport_id": transport_id,
                    "error": str(e)
                })

        db_df = pd.DataFrame(db_scores)
        db_table = mo.ui.table(db_df, label="SentianceEventos Scores", selection=None, pagination=True)

    return db_df, db_table


@app.cell
def _(db_table, mo):
    mo.vstack([
        mo.md("## Scores from SentianceEventos (Database)"),
        db_table
    ]) if db_table is not None else None
    return


@app.cell
def _(db_df, df, mo, pd):
    comparison_table = None
    merged = None

    if df is not None and db_df is not None:
        # Convert N/A to NaN for calculations
        comparison_db = db_df.replace("N/A", pd.NA).copy()

        # Merge on user and transport
        merged = pd.merge(
            df, 
            comparison_db, 
            on=["user_id", "transport_id"], 
            how="left", 
            suffixes=("_csv", "_db")
        )

        # List of scores to compare
        score_cols = ["legal", "smooth", "attention", "overall"]

        # Calculate deltas (Difference)
        for col in score_cols:
            csv_col = f"{col}_csv"
            db_col = f"{col}_db"
            delta_col = f"{col}_delta"

            # Ensure numeric for subtraction
            merged[csv_col] = pd.to_numeric(merged[csv_col], errors='coerce')
            merged[db_col] = pd.to_numeric(merged[db_col], errors='coerce')

            # Calculate absolute difference
            merged[delta_col] = (merged[csv_col] - merged[db_col]).abs()

        # Reorder columns for readability: ID, CSV, DB, Delta
        final_cols = ["user_id", "transport_id"]
        for col in score_cols:
            final_cols.extend([f"{col}_csv", f"{col}_db", f"{col}_delta"])

        comparison_table = mo.ui.table(
            merged[final_cols], 
            label="Score Comparison (CSV vs DB)", 
            selection=None, 
            pagination=True
        )

    return (comparison_table,)


@app.cell
def _(comparison_table, mo):
    mo.vstack([
        mo.md("## 📊 Score Comparison (CSV vs Database)"),
        mo.md("> Deltas show absolute difference between CSV and DB values."),
        comparison_table
    ]) if comparison_table is not None else None
    return


if __name__ == "__main__":
    app.run()

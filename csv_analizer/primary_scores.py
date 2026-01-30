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
        table = mo.ui.table(df, label="Safety Scores Grid (CSV)", selection=None, pagination=True, max_height=500)

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
        mo.md("## Safety Scores Grid (CSV)"),
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
        se_scores = []

        # Extract scores for each row
        for se_index, se_row in df.iterrows():
            se_user_id = se_row['user_id']
            se_transport_id = se_row['transport_id']

            # SQL query using %like% for transport_id in the JSON field
            se_query = f"""
            SELECT TOP 1 JSON 
            FROM SentianceEventos 
            WHERE sentianceid = '{se_user_id}' 
            AND JSON LIKE '%{se_transport_id}%'
            """

            try:
                se_res_df = mo.sql(se_query, engine=engine, output=False)

                if not se_res_df.empty:
                    se_raw_json = se_res_df.iloc[0]['JSON']
                    se_data = json.loads(se_raw_json)

                    # Extract safety scores from the JSON structure
                    se_details = se_data.get("safetyScores", {})

                    se_scores.append({
                        "user_id": se_user_id,
                        "transport_id": se_transport_id,
                        "legal": se_details.get("legalScore", "N/A"),
                        "smooth": se_details.get("smoothScore", "N/A"),
                        "attention": se_details.get("focusScore", "N/A"), # Mapping focusScore to attention
                        "overall": se_details.get("overallScore", "N/A"),
                        "harsh_accel": se_details.get("harshAccelerationScore", "N/A"),
                        "harsh_brake": se_details.get("harshBrakingScore", "N/A"),
                        "harsh_turn": se_details.get("harshTurningScore", "N/A"),
                        "call_moving": se_details.get("callWhileMovingScore", "N/A")
                    })
                else:
                    se_scores.append({
                        "user_id": se_user_id,
                        "transport_id": se_transport_id,
                        "legal": "N/A", "smooth": "N/A", "attention": "N/A", "overall": "N/A",
                        "harsh_accel": "N/A", "harsh_brake": "N/A", "harsh_turn": "N/A", "call_moving": "N/A"
                    })
            except Exception as e:
                se_scores.append({
                    "user_id": se_user_id,
                    "transport_id": se_transport_id,
                    "error": str(e)
                })

        db_df = pd.DataFrame(se_scores)
        db_table = mo.ui.table(db_df, label="SentianceEventos Scores", selection=None, pagination=True, max_height=500)
    return db_df, db_table


@app.cell
def _(db_table, mo):
    mo.vstack([
        mo.md("## Scores from SentianceEventos (Database)"),
        db_table
    ]) if db_table is not None else None
    return


@app.cell
def _(df, engine, mo, pd):
    pt_df = None
    pt_table = None

    if df is not None and engine is not None:
        pt_scores_list = []

        for pt_index, pt_row in df.iterrows():
            pt_user_id = pt_row['user_id']
            pt_transport_id = pt_row['transport_id']

            pt_query = f"""
            SELECT legal, suavidad, atencion, promedio 
            FROM PuntajesPrirmariosTr 
            WHERE usuario = '{pt_user_id}' AND viaje = '{pt_transport_id}'
            """

            try:
                pt_res_df = mo.sql(pt_query, engine=engine, output=False)

                if not pt_res_df.empty:
                    pt_data_row = pt_res_df.iloc[0]
                    pt_scores_list.append({
                        "user_id": pt_user_id,
                        "transport_id": pt_transport_id,
                        "legal": pt_data_row['legal'],
                        "smooth": pt_data_row['suavidad'],
                        "attention": pt_data_row['atencion'],
                        "overall": pt_data_row['promedio']
                    })
                else:
                    pt_scores_list.append({
                        "user_id": pt_user_id,
                        "transport_id": pt_transport_id,
                        "legal": "N/A", "smooth": "N/A", "attention": "N/A", "overall": "N/A"
                    })
            except Exception as e:
                pt_scores_list.append({
                    "user_id": pt_user_id,
                    "transport_id": pt_transport_id,
                    "error": str(e)
                })

        pt_df = pd.DataFrame(pt_scores_list)
        pt_table = mo.ui.table(pt_df, label="PuntajesPrirmariosTr Scores", selection=None, pagination=True, max_height=500)
    return pt_df, pt_table


@app.cell
def _(mo, pt_table):
    mo.vstack([
        mo.md("## Scores from PuntajesPrirmariosTr (Database)"),
        pt_table
    ]) if pt_table is not None else None
    return


@app.cell
def _(db_df, df, mo, pd, pt_df):
    comparison_table = None
    merged = None

    if df is not None and db_df is not None and pt_df is not None:
        # Convert N/A to NaN for calculations
        comparison_db = db_df.replace("N/A", pd.NA).copy()
        comparison_pt = pt_df.replace("N/A", pd.NA).copy()

        # Merge on user and transport
        merged = pd.merge(
            df, 
            comparison_db, 
            on=["user_id", "transport_id"], 
            how="left", 
            suffixes=("_csv", "_se")
        )

        merged = pd.merge(
            merged,
            comparison_pt,
            on=["user_id", "transport_id"],
            how="left"
        )
        # Rename pt columns to have _pt suffix
        merged = merged.rename(columns={
            "legal": "legal_pt",
            "smooth": "smooth_pt",
            "attention": "attention_pt",
            "overall": "overall_pt"
        })

        # List of scores to compare
        score_cols = ["legal", "smooth", "attention", "overall"]

        # Calculate deltas (Difference between first two as baseline)
        for col in score_cols:
            csv_col = f"{col}_csv"
            se_col = f"{col}_se"
            pt_col = f"{col}_pt"

            # Ensure numeric for subtraction
            merged[csv_col] = pd.to_numeric(merged[csv_col], errors='coerce')
            merged[se_col] = pd.to_numeric(merged[se_col], errors='coerce')
            merged[pt_col] = pd.to_numeric(merged[pt_col], errors='coerce')

            # Calculate absolute differences
            merged[f"{col}_csv_vs_se"] = (merged[csv_col] - merged[se_col]).abs()
            merged[f"{col}_csv_vs_pt"] = (merged[csv_col] - merged[pt_col]).abs()
            merged[f"{col}_se_vs_pt"] = (merged[se_col] - merged[pt_col]).abs()

        # Reorder columns for readability
        final_cols = ["user_id", "transport_id"]
        for col in score_cols:
            final_cols.extend([f"{col}_csv", f"{col}_se", f"{col}_pt"])
            # final_cols.extend([f"{col}_csv_vs_se", f"{col}_csv_vs_pt"]) # Optional: add deltas if needed

        comparison_table = mo.ui.table(
            merged[final_cols], 
            label="Score Comparison (CSV vs SE vs PT)", 
            selection=None, 
            pagination=True,
            max_height=500
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

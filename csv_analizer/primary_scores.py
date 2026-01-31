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
                        "focus": se_details.get("focusScore", "N/A"),
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
                        "legal": "---", "smooth": "---", "focus": "---", "overall": "---",
                        "harsh_accel": "---", "harsh_brake": "---", "harsh_turn": "---", "call_moving": "---"
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
                        "overall": pt_data_row['promedio']
                    })
                else:
                    pt_scores_list.append({
                        "user_id": pt_user_id,
                        "transport_id": pt_transport_id,
                        "legal": "---", "smooth": "---", "overall": "---"
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


@app.cell(hide_code=True)
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
        # Merge on user and transport
        merged = pd.merge(
            df, 
            db_df, 
            on=["user_id", "transport_id"], 
            how="left", 
            suffixes=("_csv", "_se")
        )

        merged = pd.merge(
            merged,
            pt_df,
            on=["user_id", "transport_id"],
            how="left"
        )
        # Rename pt columns to have _pt suffix
        merged = merged.rename(columns={
            "legal": "legal_pt",
            "smooth": "smooth_pt",
            "overall": "overall_pt"
        })

        # List of scores to compare
        score_cols = ["legal", "smooth", "overall"]

        # Reorder columns for readability
        final_cols = ["user_id", "transport_id"]
        for col in score_cols:
            final_cols.extend([f"{col}_csv", f"{col}_se", f"{col}_pt"])

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
        comparison_table
    ]) if comparison_table is not None else None
    return


@app.cell
def _(df, engine, mo, pd):
    st_df = None
    st_table = None

    if df is not None and engine is not None:
        st_scores_list = []

        for st_index, st_row in df.iterrows():
            st_user_id = st_row['user_id']
            st_transport_id = st_row['transport_id']

            st_query = f"""
            SELECT concentracion, aceleracion_fuerte, frenado_fuerte, curvas_fuertes, anticipacion, celular_fijo, eventos_fuertes 
            FROM PuntajesSecundariosTr 
            WHERE usuario = '{st_user_id}' AND viaje = '{st_transport_id}'
            """

            try:
                st_res_df = mo.sql(st_query, engine=engine, output=False)

                if not st_res_df.empty:
                    st_data_row = st_res_df.iloc[0]
                    st_scores_list.append({
                        "user_id": st_user_id,
                        "transport_id": st_transport_id,
                        "concentration": st_data_row['concentracion'],
                        "hard_accel": st_data_row['aceleracion_fuerte'],
                        "hard_brake": st_data_row['frenado_fuerte'],
                        "hard_turns": st_data_row['curvas_fuertes'],
                        "anticipation": st_data_row['anticipacion'],
                        "phone_fixed": st_data_row['celular_fijo'],
                        "strong_events": st_data_row['eventos_fuertes']
                    })
                else:
                    st_scores_list.append({
                        "user_id": st_user_id,
                        "transport_id": st_transport_id,
                        "concentration": "---", "hard_accel": "---", "hard_brake": "---", "hard_turns": "---",
                        "anticipation": "---", "phone_fixed": "---", "strong_events": "---"
                    })
            except Exception as e:
                st_scores_list.append({
                    "user_id": st_user_id,
                    "transport_id": st_transport_id,
                    "error": str(e)
                })

        st_df = pd.DataFrame(st_scores_list)
        st_table = mo.ui.table(st_df, label="PuntajesSecundariosTr Scores", selection=None, pagination=True, max_height=500)
    return st_df, st_table


@app.cell(hide_code=True)
def _(mo, st_table):
    mo.vstack([
        mo.md("## Scores from PuntajesSecundariosTr (Database)"),
        st_table
    ]) if st_table is not None else None
    return


@app.cell(hide_code=True)
def _(pd):
    sec_csv_path = "../csv/secondary_safety_scores_transports.csv"
    sec_df = None
    if pd.io.common.file_exists(sec_csv_path):
        sec_df = pd.read_csv(sec_csv_path)
    return (sec_df,)


@app.cell(hide_code=True)
def _(db_df, df, mo, pd, sec_df, st_df):
    multi_comparison_table = None
    if all(x is not None for x in [df, db_df, st_df, sec_df]):
        # Start with primary attention
        comp_df = df[['user_id', 'transport_id', 'attention']].rename(columns={'attention': 'attention_primary'})

        # Merge focus from db_df (SentianceEventos)
        comp_df = pd.merge(
            comp_df,
            db_df[['user_id', 'transport_id', 'focus']].rename(columns={'focus': 'focus_se_db'}),
            on=['user_id', 'transport_id'],
            how='left'
        )

        # Merge concentration from st_df (PuntajesSecundariosTr)
        comp_df = pd.merge(
            comp_df,
            st_df[['user_id', 'transport_id', 'concentration']].rename(columns={'concentration': 'concentration_db'}),
            on=['user_id', 'transport_id'],
            how='left'
        )

        # Merge focus from secondary CSV
        comp_df = pd.merge(
            comp_df,
            sec_df[['user_id', 'transport_id', 'focus']].rename(columns={'focus': 'focus_secondary_csv'}),
            on=['user_id', 'transport_id'],
            how='left'
        )

        multi_comparison_table = mo.ui.table(
            comp_df,
            label="Focus & Concentration Multi-Source Comparison",
            selection=None,
            pagination=True,
            max_height=500
        )

    mo.vstack([
        mo.md("## 🎯 Focus & Concentration Multi-Source Comparison"),
        mo.md("> Side-by-side comparison across Primary CSV, SentianceEventos (DB), PuntajesSecundariosTr (DB), and Secondary CSV."),
        multi_comparison_table
    ]) if multi_comparison_table is not None else None
    return


if __name__ == "__main__":
    app.run()

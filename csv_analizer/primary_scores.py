import marimo

__generated_with = "0.19.6"
app = marimo.App(width="full")


@app.cell
def _():
    # Importación de librerías y configuración de variables de entorno
    import marimo as mo
    import pandas as pd
    import os
    import json
    import sqlalchemy
    from sqlalchemy import create_engine
    from dotenv import load_dotenv

    # Cargar .env desde el directorio marimo_lab
    # Notebook actual: tools/csv_analizer/primary_scores.py
    # .env: tools/marimo_lab/.env
    env_path = os.path.abspath(os.path.join(os.getcwd(), "../marimo_lab/.env"))
    load_dotenv(env_path)
    return create_engine, json, mo, os, pd


@app.cell
def _(mo):
    # Título y descripción del notebook
    mo.md(r"""
    # Analizador de Puntajes de Seguridad (Safety Scores)
    Este notebook muestra el contenido de `primary_safety_scores_transports.csv` y recupera los puntajes correspondientes de la base de datos para su comparación.
    """)
    return


@app.cell
def _(create_engine, mo, os):
    # Configuración de la conexión a la base de datos SQL Server
    # Credenciales de la base de datos de las variables de entorno
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
        db_status = mo.callout("Faltan credenciales de base de datos en .env", kind="warn")
    return db_status, engine


@app.cell
def _(mo, pd):
    # Carga del archivo CSV principal con puntajes de seguridad
    csv_path = "../csv/primary_safety_scores_transports.csv"

    df = None
    table = None
    stats_table = None

    if pd.io.common.file_exists(csv_path):
        df = pd.read_csv(csv_path)
        table = mo.ui.table(df, label="Grilla de Puntajes (CSV Primario)", selection=None, pagination=True, max_height=500)

        # Estadísticas resumidas
        stats = df.describe().reset_index()
        stats_table = mo.ui.table(stats, label="Estadísticas")
    else:
        table = mo.callout(f"File not found: {csv_path}", kind="danger")
    return df, stats_table, table


@app.cell
def _(db_status, mo, stats_table, table):
    # Visualización del contenido del CSV y estadísticas generales
    mo.vstack([
        db_status,
        mo.md("## Safety Scores (primary_safety_scores_transports.csv)"),
        table,
        mo.md("## Estadísticas"),
        stats_table
    ]) if table is not None else None
    return


@app.cell
def _(df, engine, json, mo, pd):
    # Obtención de puntajes desde SentianceEventos (JSON en base de datos)
    db_df = None
    db_table = None

    if df is not None and engine is not None:
        se_scores = []

        with mo.status.spinner(title="Consultando SentianceEventos...") as _spinner:
            # Extraer puntajes para cada fila
            se_total_rows = len(df)
            for se_i, (se_index, se_row) in enumerate(df.iterrows()):
                _spinner.update(title=f"Consultando SentianceEventos... ({se_i+1}/{se_total_rows})")
                se_user_id = se_row['user_id']
                se_transport_id = se_row['transport_id']

                # Consulta SQL usando %like% para el transport_id en el campo JSON
                se_query = f"""
                SELECT TOP 1 JSON 
                FROM SentianceEventos 
                WHERE sentianceid = '{se_user_id}'
                AND tipo = 'DrivingInsights'
                AND JSON LIKE '%{se_transport_id}%'
                """

                try:
                    se_res_df = mo.sql(se_query, engine=engine, output=False)

                    if not se_res_df.empty:
                        se_raw_json = se_res_df.iloc[0]['JSON']
                        se_data = json.loads(se_raw_json)

                        # Extraer puntajes de seguridad de la estructura JSON
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
                            "harsh_events": "---",  # No presente en el JSON de SE proporcionado
                            "call_moving": se_details.get("callWhileMovingScore", "N/A")
                        })
                    else:
                        se_scores.append({
                            "user_id": se_user_id,
                            "transport_id": se_transport_id,
                            "legal": "---", "smooth": "---", "focus": "---", "overall": "---",
                            "harsh_accel": "---", "harsh_brake": "---", "harsh_turn": "---", "harsh_events": "---", "call_moving": "---"
                        })
                except Exception as e:
                    se_scores.append({
                        "user_id": se_user_id,
                        "transport_id": se_transport_id,
                        "error": str(e)
                    })

        db_df = pd.DataFrame(se_scores)
        db_table = mo.ui.table(db_df, label="Puntajes de SentianceEventos", selection=None, pagination=True, max_height=500)
    return db_df, db_table


@app.cell
def _(db_table, mo):
    # Visualización de los puntajes obtenidos de SentianceEventos
    mo.vstack([
        mo.md("## Puntajes en SentianceEventos (Base de Datos)"),
        db_table
    ]) if db_table is not None else None
    return


@app.cell
def _(df, engine, mo, pd):
    # Obtención de puntajes desde la tabla PuntajesPrirmariosTr (Base de datos)
    pt_df = None
    pt_table = None

    if df is not None and engine is not None:
        pt_scores_list = []

        with mo.status.spinner(title="Consultando PuntajesPrirmariosTr...") as _spinner:
            pt_total_rows = len(df)
            for pt_i, (pt_index, pt_row) in enumerate(df.iterrows()):
                _spinner.update(title=f"Consultando PuntajesPrirmariosTr... ({pt_i+1}/{pt_total_rows})")
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
        pt_table = mo.ui.table(pt_df, label="Puntajes de PuntajesPrirmariosTr", selection=None, pagination=True, max_height=500)
    return pt_df, pt_table


@app.cell
def _(mo, pt_table):
    # Visualización de los puntajes obtenidos de PuntajesPrirmariosTr
    mo.vstack([
        mo.md("## Puntajes en PuntajesPrirmariosTr (Base de Datos)"),
        pt_table
    ]) if pt_table is not None else None
    return


@app.cell
def _(db_df, df, mo, pd, pt_df):
    # Cálculo y visualización de la comparativa de puntajes primarios
    comparison_table = None
    merged = None

    if df is not None and db_df is not None and pt_df is not None:
        # Unir por usuario y transporte
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
        # Renombrar columnas pt para tener el sufijo _pt
        merged = merged.rename(columns={
            "legal": "legal_pt",
            "smooth": "smooth_pt",
            "overall": "overall_pt"
        })

        # Lista de puntajes a comparar
        score_cols = ["legal", "smooth", "overall"]

        # Reordenar columnas para legibilidad
        final_cols = ["user_id", "transport_id"]
        for col in score_cols:
            final_cols.extend([f"{col}_csv", f"{col}_se", f"{col}_pt"])

        comparison_table = mo.ui.table(
            merged[final_cols], 
            label="Comparativa (CSV vs SentianceEventos vs PuntajesPrimariosTr)", 
            selection=None, 
            pagination=True,
            max_height=500
        )
    return (comparison_table,)


@app.cell
def _(comparison_table, mo):
    # Renderizado de la tabla comparativa de puntajes primarios
    mo.vstack([
        mo.md("## 📊 Comparativa (primary_safety_scores_transports.csv vs SentianceEventos vs PuntajesPrimariosTr)"),
        comparison_table
    ]) if comparison_table is not None else None
    return


@app.cell
def _(df, engine, mo, pd):
    # Obtención de puntajes secundarios desde la tabla PuntajesSecundariosTr
    st_df = None
    st_table = None

    if df is not None and engine is not None:
        st_scores_list = []

        with mo.status.spinner(title="Consultando PuntajesSecundariosTr...") as _spinner:
            st_total_rows = len(df)
            for st_i, (st_index, st_row) in enumerate(df.iterrows()):
                _spinner.update(title=f"Consultando PuntajesSecundariosTr... ({st_i+1}/{st_total_rows})")
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
        st_table = mo.ui.table(st_df, label="Puntajes de PuntajesSecundariosTr", selection=None, pagination=True, max_height=500)
    return st_df, st_table


@app.cell
def _(mo, st_table):
    # Visualización de los puntajes secundarios obtenidos de la base de datos
    mo.vstack([
        mo.md("## Scores en PuntajesSecundariosTr (Database)"),
        st_table
    ]) if st_table is not None else None
    return


@app.cell(hide_code=True)
def _(pd):
    # Carga del archivo CSV secundario (secondary_safety_scores_transports.csv)
    sec_csv_path = "../csv/secondary_safety_scores_transports.csv"
    sec_df = None
    if pd.io.common.file_exists(sec_csv_path):
        sec_df = pd.read_csv(sec_csv_path)
    return (sec_df,)


@app.cell
def _(db_df, df, mo, pd, sec_df, st_df):
    # Comparativa multi-fuente de Focus y Concentration (Primary CSV, SE, PT, y Secondary CSV)
    multi_comparison_table = None
    if all(x is not None for x in [df, db_df, st_df, sec_df]):
        # Comenzar con la atención primaria
        comp_df = df[['user_id', 'transport_id', 'attention']].rename(columns={'attention': 'attention_primary'})

        # Unir focus de db_df (SentianceEventos)
        comp_df = pd.merge(
            comp_df,
            db_df[['user_id', 'transport_id', 'focus']].rename(columns={'focus': 'focus_se_db'}),
            on=['user_id', 'transport_id'],
            how='left'
        )

        # Unir concentración de st_df (PuntajesSecundariosTr)
        comp_df = pd.merge(
            comp_df,
            st_df[['user_id', 'transport_id', 'concentration']].rename(columns={'concentration': 'concentration_db'}),
            on=['user_id', 'transport_id'],
            how='left'
        )

        # Unir focus del CSV secundario
        comp_df = pd.merge(
            comp_df,
            sec_df[['user_id', 'transport_id', 'focus']].rename(columns={'focus': 'focus_secondary_csv'}),
            on=['user_id', 'transport_id'],
            how='left'
        )

        multi_comparison_table = mo.ui.table(
            comp_df,
            label="Comparativa entre focus y concentración",
            selection=None,
            pagination=True,
            max_height=500
        )

    mo.vstack([
        mo.md("## 🎯 Comparativa entre focus y concentración"),
        mo.md("> Comparativa entre primary_safety_scores_transports.csv, SentianceEventos (DB), PuntajesSecundariosTr (DB) y secondary_safety_scores_transports.csv."),
        multi_comparison_table
    ]) if multi_comparison_table is not None else None
    return


@app.cell
def _(mo, sec_df):
    # Visualización del CSV secundario (secondary_safety_scores_transports.csv)
    mo.vstack([
        mo.md("## Puntajes de Seguridad Secundarios (CSV)"),
        mo.ui.table(sec_df, label="Grilla de Puntajes (CSV Secundario)", selection=None, pagination=True, max_height=500)
    ]) if sec_df is not None else mo.md("Esperando archivo CSV secundario...")
    return


@app.cell
def _(db_df, mo, pd, sec_df, st_df):
    # Comparativa multi-fuente de Eventos Fuertes (Aceleración, Frenado, Giro)
    harsh_comparison_table = None
    
    if not all(x is None for x in [db_df, st_df, sec_df]):
        # Unir SE (db_df) si existe
        if db_df is not None:
            cols_se = ['user_id', 'transport_id', 'harsh_accel', 'harsh_brake', 'harsh_turn', 'harsh_events']
            harsh_comp_df = db_df[cols_se].rename(
                columns={
                    'harsh_accel': 'acel_se', 
                    'harsh_brake': 'freno_se', 
                    'harsh_turn': 'giro_se',
                    'harsh_events': 'env_se'
                }
            )
        else:
            harsh_comp_df = pd.DataFrame(columns=['user_id', 'transport_id'])

        # Unir PT (st_df) si existe
        if st_df is not None:
            pt_to_merge = st_df[['user_id', 'transport_id', 'hard_accel', 'hard_brake', 'hard_turns', 'strong_events']].rename(
                columns={
                    'hard_accel': 'acel_pt', 
                    'hard_brake': 'freno_pt', 
                    'hard_turns': 'giro_pt',
                    'strong_events': 'env_pt'
                }
            )
            harsh_comp_df = pd.merge(harsh_comp_df, pt_to_merge, on=['user_id', 'transport_id'], how='outer')

        # Unir con CSV secundario si existe
        if sec_df is not None:
            csv_to_merge = sec_df[['user_id', 'transport_id', 'harsh_acceleration', 'harsh_braking', 'harsh_turning', 'harsh_events']].rename(
                columns={
                    'harsh_acceleration': 'acel_csv',
                    'harsh_braking': 'freno_csv',
                    'harsh_turning': 'giro_csv',
                    'harsh_events': 'env_csv'
                }
            )
            harsh_comp_df = pd.merge(harsh_comp_df, csv_to_merge, on=['user_id', 'transport_id'], how='outer')

        # Reordenar columnas para agrupar por tipo de evento
        ordered_cols = ['user_id', 'transport_id', 
                        'acel_se', 'acel_pt', 'acel_csv',
                        'freno_se', 'freno_pt', 'freno_csv',
                        'giro_se', 'giro_pt', 'giro_csv',
                        'env_se', 'env_pt', 'env_csv']
        
        # Filtrar columnas que existan
        ordered_cols = [c for c in ordered_cols if c in harsh_comp_df.columns]

        harsh_comparison_table = mo.ui.table(
            harsh_comp_df[ordered_cols],
            label="Comparativa de Eventos Fuertes",
            selection=None,
            pagination=True,
            max_height=500
        )

    mo.vstack([
        mo.md("## 🏎️ Comparativa de Eventos Fuertes (Aceleración, Frenado, Giro)"),
        mo.md("> Comparativa entre SentianceEventos (DB), PuntajesSecundariosTr (DB) y secondary_safety_scores_transports.csv."),
        harsh_comparison_table
    ]) if harsh_comparison_table is not None else mo.md("Omitiendo comparativa de eventos fuertes (faltan fuentes de datos)")
    return


if __name__ == "__main__":
    app.run()

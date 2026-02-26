import marimo

__generated_with = "0.19.6"
app = marimo.App(width="full")

@app.cell
def setup():
    import marimo as mo
    import pandas as pd
    import os
    import json
    import sqlalchemy
    from sqlalchemy import create_engine
    from dotenv import load_dotenv

    env_path = os.path.abspath(os.path.join(os.getcwd(), "../marimo_lab/.env"))
    load_dotenv(env_path)
    return create_engine, json, mo, os, pd

@app.cell
def intro_ui(mo):
    mo.md(r"""
    # Analizador y Extractor de Viajes de MovDebug_Eventos
    Este notebook extrae múltiples tipos de eventos (`tipo`) desde la tabla `MovDebug_Eventos` para aplanar y listar todas las instancias de un mismo viaje (`IN_TRANSPORT`). El objetivo es observar cómo se reporta y actualiza un mismo viaje a lo largo del tiempo.
    """)
    return

@app.cell
def db_conn(create_engine, mo, os):
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    port = os.getenv("DB_PORT", "9433")

    if all([server, database, username, password]):
        connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"
        engine = create_engine(connection_string)
        db_status = mo.md(f"✅ Conectado a `{database}` en `{server}`")
    else:
        engine = None
        db_status = mo.callout("Faltan credenciales de base de datos en .env", kind="warn")
    return db_status, engine

@app.cell
def execute_extraction(engine, json, mo, pd):
    tipos_target = "('DrivingInsights', 'UserContextUpdate', 'requestUserContext', 'TimelineUpdateListener', 'TimelineEventById')"
    
    # Check count first to setup a precise progress bar
    count_query = f"SELECT COUNT(*) AS total FROM MovDebug_Eventos WHERE tipo IN {tipos_target}"
    
    extracted_trips = []
    extraction_complete = False
    
    if engine is not None:
        try:
            total_rows_df = pd.read_sql(count_query, engine)
            total_rows = int(total_rows_df.iloc[0]['total'])
            
            # Use chunks to not overwhelm memory and keep progress bar updating
            chunk_size = 1000
            
            with mo.status.progress_bar(total=total_rows, title="Extrayendo y parseando JSON (MovDebug_Eventos)", subtitle="Iniciando...") as pbar:
                data_query = f"SELECT id, tipo, sentianceid, JSON FROM MovDebug_Eventos WHERE tipo IN {tipos_target} ORDER BY id ASC"
                
                # Using execution stream
                for chunk in pd.read_sql(data_query, engine, chunksize=chunk_size):
                    for idx, row in chunk.iterrows():
                        db_record_id = row['id']
                        tipo = row['tipo']
                        user_id = row['sentianceid']
                        raw_json = row['JSON']
                        
                        if not raw_json or pd.isna(raw_json):
                            continue
                            
                        try:
                            parsed = json.loads(raw_json)
                        except:
                            continue
                            
                        # Logic depending on type
                        if tipo == 'DrivingInsights':
                            transport_event = parsed.get("transportEvent")
                            if transport_event and transport_event.get("type") == "IN_TRANSPORT":
                                extracted_trips.append({
                                    "db_record_id": db_record_id,
                                    "source_tipo": tipo,
                                    "source_criteria": ",".join(parsed.get("criteria", [])) if isinstance(parsed.get("criteria"), list) else "",
                                    "user_id": user_id,
                                    "trip_id": transport_event.get("id"),
                                    "transportMode": transport_event.get("transportMode"),
                                    "isProvisional": transport_event.get("isProvisional"),
                                    "startTime": transport_event.get("startTime"),
                                    "endTime": transport_event.get("endTime"),
                                    "distance": transport_event.get("distance"),
                                    "durationInSeconds": transport_event.get("durationInSeconds"),
                                    "waypoints_count": len(transport_event.get("waypoints", []))
                                })
                                
                        elif tipo in ("UserContextUpdate", "requestUserContext"):
                            # Looking inside events array or userContext.events array
                            events = parsed.get("events")
                            if events is None and "userContext" in parsed:
                                events = parsed.get("userContext", {}).get("events")
                                
                            if events and isinstance(events, list):
                                for event in events:
                                    if event.get("type") == "IN_TRANSPORT":
                                        extracted_trips.append({
                                            "db_record_id": db_record_id,
                                            "source_tipo": tipo,
                                            "source_criteria": ",".join(parsed.get("criteria", [])) if isinstance(parsed.get("criteria"), list) else "",
                                            "user_id": user_id,
                                            "trip_id": event.get("id"),
                                            "transportMode": event.get("transportMode"),
                                            "isProvisional": event.get("isProvisional"),
                                            "startTime": event.get("startTime"),
                                            "endTime": event.get("endTime"),
                                            "distance": event.get("distance"),
                                            "durationInSeconds": event.get("durationInSeconds"),
                                            "waypoints_count": len(event.get("waypoints", []))
                                        })
                        
                        elif tipo in ("TimelineUpdateListener", "TimelineEventById"):
                            if parsed.get("type") == "IN_TRANSPORT":
                                extracted_trips.append({
                                    "db_record_id": db_record_id,
                                    "source_tipo": tipo,
                                    "source_criteria": ",".join(parsed.get("criteria", [])) if isinstance(parsed.get("criteria"), list) else "",
                                    "user_id": user_id,
                                    "trip_id": parsed.get("id"),
                                    "transportMode": parsed.get("transportMode"),
                                    "isProvisional": parsed.get("isProvisional"),
                                    "startTime": parsed.get("startTime"),
                                    "endTime": parsed.get("endTime"),
                                    "distance": parsed.get("distance"),
                                    "durationInSeconds": parsed.get("durationInSeconds"),
                                    "waypoints_count": len(parsed.get("waypoints", []))
                                })

                    pbar.update(increment=len(chunk), subtitle=f"Procesando chunk de {chunk_size} filas...")
                    
            extraction_complete = True
            
        except Exception as e:
            mo.md(f"Error extracting data: {str(e)}")
            
    return extraction_complete, extracted_trips, total_rows

@app.cell
def process_extracted_data(extracted_trips, extraction_complete, mo, os, pd):
    final_df = None
    csv_saved_status = None
    
    if extraction_complete and len(extracted_trips) > 0:
        final_df = pd.DataFrame(extracted_trips)
        
        # Group duplicates logically by ordering
        # Sort by Trip ID, then chronologically by the Db Record ID to see changes over time
        final_df = final_df.sort_values(by=['trip_id', 'db_record_id'], ascending=[True, True])
        
        # Force these columns to be categorical for better Marimo filtering
        final_df['transportMode'] = final_df['transportMode'].fillna('UNAVAILABLE').astype('category')
        final_df['source_tipo'] = final_df['source_tipo'].astype('category')
        
        # Force these columns to be explicit strings instead of generic 'object'
        # This enables the text-search filter in the Marimo ui.table header.
        final_df['trip_id'] = final_df['trip_id'].astype('string')
        final_df['user_id'] = final_df['user_id'].astype('string')
        final_df['source_criteria'] = final_df['source_criteria'].astype('string')
        
        save_path = os.path.abspath(os.path.join(os.getcwd(), "../csv/movdebug_all_trip_instances.csv"))
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            final_df.to_csv(save_path, index=False)
            csv_saved_status = mo.md(f"✅ CSV guardado exitosamente con **{len(final_df)}** viajes encontrados ({len(final_df['trip_id'].unique())} únicos) en: `{save_path}`")
        except Exception as e:
            csv_saved_status = mo.callout(f"Error al guardar CSV: {str(e)}", kind="danger")
            
    elif extraction_complete:
        csv_saved_status = mo.md("No se encontraron eventos `IN_TRANSPORT` en la tabla bajo los tipos especificados.")
        
    return csv_saved_status, final_df

@app.cell
def verify_di_overlap(final_df, mo, pd):
    if final_df is not None:
        # Filter for unique trip IDs in both types
        di_trips = set(final_df[final_df["source_tipo"] == "DrivingInsights"]["trip_id"].unique())
        ucu_trips = set(final_df[final_df["source_tipo"] == "UserContextUpdate"]["trip_id"].unique())
        
        total_di = len(di_trips)
        matches = di_trips.intersection(ucu_trips)
        match_count = len(matches)
        
        missing = di_trips - ucu_trips
        
        if total_di > 0:
            percent = (match_count / total_di) * 100
            if match_count == total_di:
                result = mo.callout(
                    f"✅ Verificación exitosa: Los {total_di} viajes de DrivingInsights están presentes en UserContextUpdate (100% match).",
                    kind="success"
                )
            else:
                # Extract transportMode and isProvisional for these missing trips from the DrivingInsights original records
                missing_info = final_df[
                    (final_df["trip_id"].isin(missing)) & 
                    (final_df["source_tipo"] == "DrivingInsights")
                ][["trip_id", "transportMode", "isProvisional"]].drop_duplicates()

                result = mo.vstack([
                    mo.callout(
                        f"⚠️ Verificación parcial: {match_count} de {total_di} viajes de DrivingInsights ({percent:.2f}%) encontrados en UserContextUpdate.",
                        kind="warn"
                    ),
                    mo.md(f"**IDs Faltantes en UserContextUpdate ({len(missing)}):**"),
                    mo.ui.table(missing_info) if len(missing) > 0 else mo.md("Ninguno")
                ])
        else:
            result = mo.md("No hay viajes de `DrivingInsights` para comparar.")
    else:
        result = None
    return matches, result

# =============================================================================
# CELDA: MATRIZ DE VIABILIDAD Y ANÁLISIS DE COBERTURA
# =============================================================================
# Esta celda agrupa todos los eventos por `trip_id` para crear una matriz comparativa.
# Permite identificar qué viajes fueron detectados por `DrivingInsights`, cuáles
# por `UserContextUpdate` (con criterio `CURRENT_EVENT`), y calcular estadísticas
# de solapamiento y anomalías.
#
# Depende de: `final_df` (Dataframe consolidado) y `mo` (Marimo UI).
@app.cell
def viability_matrix(final_df, mo):
    if final_df is not None:
        # Group by trip_id to build the matrix
        matrix = final_df.groupby("trip_id").agg(
            has_DrivingInsights=("source_tipo", lambda x: (x == "DrivingInsights").any()),
            has_UCU_CurrentEvent=("source_criteria", lambda x: x.str.contains("CURRENT_EVENT", na=False).any()),
            count_UCU_CurrentEvent=("source_criteria", lambda x: x.str.contains("CURRENT_EVENT", na=False).sum()),
            transportMode=("transportMode", "first")
        ).reset_index()
        
        # Sort so trips without DrivingInsights but with UCU_CurrentEvent appear at top (to check coverage)
        matrix = matrix.sort_values(by=["has_DrivingInsights", "has_UCU_CurrentEvent"], ascending=[True, False])
        
        matrix_ui = mo.ui.table(
            matrix,
            label="Matriz de Viabilidad: DrivingInsights vs UserContextUpdate (CURRENT_EVENT)",
            pagination=True
        )
        
        # Coverage check
        total_trips = len(matrix)
        di_only = matrix[(matrix["has_DrivingInsights"] == True) & (matrix["has_UCU_CurrentEvent"] == False)]
        ucu_only = matrix[(matrix["has_DrivingInsights"] == False) & (matrix["has_UCU_CurrentEvent"] == True)]
        # Missing entirely from both
        neither_trips_ids = matrix[(matrix["has_DrivingInsights"] == False) & (matrix["has_UCU_CurrentEvent"] == False)]["trip_id"]
        
        def get_pct(count):
            return f"({(count / total_trips * 100):.1f}%)" if total_trips > 0 else "(0.0%)"

        coverage_status = mo.md(f"""
        ### Análisis de Cobertura (Total Trips Únicos: {total_trips})
        - **Trips con DrivingInsights:** {matrix["has_DrivingInsights"].sum()} {get_pct(matrix["has_DrivingInsights"].sum())}
        - **Trips con UCU (CURRENT_EVENT):** {matrix["has_UCU_CurrentEvent"].sum()} {get_pct(matrix["has_UCU_CurrentEvent"].sum())}
        - **Trips SOLO en DrivingInsights (Sin UCU CE):** {len(di_only)} {get_pct(len(di_only))}
        - **Trips SOLO en UCU (Sin DrivingInsights):** {len(ucu_only)} {get_pct(len(ucu_only))}
        - **Trips SIN DrivingInsights NI UCU (CURRENT_EVENT):** {len(neither_trips_ids)} {get_pct(len(neither_trips_ids))}
        """)
        
        matrix_display = mo.vstack([
            coverage_status,
            matrix_ui
        ])
    else:
        matrix_display = None
        neither_trips_ids = None
    return coverage_status, di_only, matrix, matrix_display, matrix_ui, neither_trips_ids, ucu_only

@app.cell
def missing_from_both_table(final_df, mo, neither_trips_ids):
    if final_df is not None and neither_trips_ids is not None and len(neither_trips_ids) > 0:
        # Filter the full generic dataframe to only keep the rows of these strange trips
        neither_df = final_df[final_df["trip_id"].isin(neither_trips_ids)]
        
        neither_table_ui = mo.ui.table(
            neither_df,
            label=f"Viajes sin DI ni UCU CURRENT_EVENT ({len(neither_trips_ids)} trips / {len(neither_df)} eventos)",
            pagination=True,
            max_height=600
        )
        
        neither_display = mo.vstack([
            mo.md(f"### Viajes Ausentes en Ambos (Anómalos)"),
            mo.md("Estos viajes existen en *MovDebug_Eventos* pero no provienen ni de `DrivingInsights` ni de `UserContextUpdate` con `CURRENT_EVENT`. Generalmente provienen de `requestUserContext` o tipos misceláneos."),
            neither_table_ui
        ])
    else:
        neither_display = mo.md("*No hay viajes que falten en ambos orígenes simultáneamente.*") if final_df is not None else None
    return neither_df, neither_display, neither_table_ui

@app.cell
def render_results(
    csv_saved_status,
    db_status,
    final_df,
    matrix_display,
    mo,
    neither_display,
    result,
):
    if final_df is not None:
        table_ui = mo.ui.table(
            final_df,
            label="Grilla de Viajes (agrupados por trip_id)",
            pagination=True,
            max_height=600
        )
        
        display = mo.vstack([
            db_status,
            csv_saved_status,
            mo.md("### Verificación de Cobertura (DI vs UCU Total)"),
            result,
            mo.md("### Matriz de Viabilidad (DI vs UCU CURRENT_EVENT)"),
            matrix_display,
            mo.md("### Vista Previa de Datos Completos"),
            table_ui,
            neither_display
        ])
    else:
        display = mo.vstack([
            db_status,
            mo.md("Ejecutando extracción... por favor espere.")
        ])
        
    display
    return display, table_ui

if __name__ == "__main__":
    app.run()

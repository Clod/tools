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
def render_results(csv_saved_status, db_status, final_df, mo):
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
            mo.md("### Vista Previa de Datos"),
            table_ui
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

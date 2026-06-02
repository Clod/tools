"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   EXPLORADOR DE DATOS SENTIANCE - MARIMO                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ QUÉ HACE ESTE NOTEBOOK:                                                      ║
║ - Se conecta a una base de datos SQL Server para consultar eventos Sentiance ║
║ - Permite filtrar por ID de Sentiance y rango de fecha/hora                  ║
║ - Muestra resultados en una tabla interactiva con selección de filas         ║
║ - Ofrece un visor detallado de campos JSON para las filas seleccionadas      ║
║ - Extrae y visualiza datos geográficos (lugares/rutas) en un mapa            ║
║   interactivo usando leafmap                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ CÓMO EJECUTAR ESTE NOTEBOOK:                                                 ║
║                                                                              ║
║ 1. CON UV (Recomendado):                                                     ║
║    $ uv run marimo edit sentiance_data_explorer.py                           ║
║    Esto instalará automáticamente todas las dependencias necesarias.         ║
║                                                                              ║
║ 2. MODO EDICIÓN (Tradicional):                                               ║
║    $ marimo edit sentiance_data_explorer.py                                  ║
║    Abre el IDE completo en el navegador para editar código y ver salidas     ║
║                                                                              ║
║ 3. MODO EJECUCIÓN (Interfaz limpia):                                         ║
║    $ marimo run sentiance_data_explorer.py                                   ║
║    Abre la app final - los usuarios solo ven salidas y widgets de interfaz   ║
║                                                                              ║
║ 4. EXPORTAR A HTML (Snapshot estático):                                      ║
║    $ marimo export html sentiance_data_explorer.py -o app.html               ║
║    Crea un archivo HTML estático (sin interactividad, solo una captura)      ║
║                                                                              ║
║ 5. CONVERTIR A JUPYTER (Migración):                                          ║
║    $ marimo export ipynb sentiance_data_explorer.py -o app.ipynb             ║
║    Convierte al formato de notebook de Jupyter                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# =============================================================================
# IMPORTACIÓN DE MARIMO E INICIALIZACIÓN DE LA APP
# =============================================================================
# Todo notebook de marimo DEBE comenzar con esta importación. Es la librería principal.
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "sqlalchemy",
#     "pymssql",
#     "leafmap",
#     "python-dotenv",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _():
    # ==========================================================================
    # IMPORTACIONES DENTRO DE CELDAS
    # ==========================================================================
    # En marimo, las importaciones se suelen hacer dentro de las celdas y se DEVUELVEN.
    # Esto las hace disponibles para otras celdas que las necesiten.
    # 
    # ¿POR QUÉ? Porque marimo rastrea dependencias a través de la sentencia return.
    # Si importas a nivel superior (fuera de celdas), marimo no puede rastrear qué se usa.

    import marimo as mo  # 'mo' es el alias convencional para marimo
    import pandas as pd
    import json
    import sqlalchemy
    import leafmap
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # ==========================================================================
    # SENTENCIA RETURN - EL CORAZÓN DE LA REACTIVIDAD DE MARIMO
    # ==========================================================================
    # TODO lo que una celda quiera "exportar" a otras celdas DEBE ser devuelto.
    # 
    # Formatos de retorno:
    #   return (var1, var2, var3)  - Tupla: exporta múltiples variables
    #   return (single_var,)       - Una sola variable (¡nota la coma final!)
    #   return                     - No exporta nada (la celda es un "sumidero")
    #
    # Las variables devueltas se vuelven disponibles como PARÁMETROS para otras celdas.
    return json, leafmap, mo, os, pd, sqlalchemy


@app.cell(hide_code=True)
def _(mo):
    # ==========================================================================
    # mo.md() - RENDERIZADO DE MARKDOWN
    # ==========================================================================
    # mo.md() convierte texto markdown en salida HTML formateada.
    # 
    # IMPORTANTE: La ÚLTIMA expresión de una celda se muestra automáticamente.
    # No necesitas print() - solo pon la expresión como la última línea.
    #
    # Soporta markdown completo: encabezados, negrita, cursiva, bloques de código, etc.
    # ¡También soporta emojis directamente en el texto! 🎉
    mo.md("""
    # ¡Bienvenido a Sentiance Data Explorer! 🌊
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Conexión a SQL Server
    Para conectarnos a SQL Server, usaremos `sqlalchemy` y `pymssql`.
    Puede usar la celda de abajo para definir su cadena de conexión.
    """)
    return


@app.cell(hide_code=True)
def _(mo, os, sqlalchemy):
    # Credenciales de base de datos desde variables de entorno
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    # El puerto por defecto para SQL Server suele ser 1433, pero aquí se usa 9433
    port = os.getenv("DB_PORT", "9433")

    # Validar que todas las variables requeridas existan
    required_vars = {
        "DB_SERVER": server,
        "DB_NAME": database,
        "DB_USER": username,
        "DB_PASS": password
    }
    missing = [v for v, val in required_vars.items() if not val]

    if missing:
        msg = mo.md(f"""
        ### ⚠️ Configuración incompleta (.env)

        No se pudieron encontrar todas las credenciales necesarias. Asegúrese de que el archivo `.env` existe y tiene el siguiente formato:

        ```env
        DB_SERVER=servidor.dominio.com
        DB_NAME=NombreDeLaBaseDeDatos
        DB_USER=usuario_sql
        DB_PASS=contraseña_segura
        DB_PORT=9433
        ```

        **Variables faltantes:** {", ".join([f"`{m}`" for m in missing])}
        """).callout(kind="warn")
        mo.stop(True, msg)

    try:
        with mo.status.spinner(title="Estableciendo conexión con la base de datos..."):
            connection_string = f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"
            engine = sqlalchemy.create_engine(connection_string)
            # Validar la conexión inmediatamente
            with engine.connect() as _conn:
                pass
    except Exception as e:
        msg = mo.md(f"""
        ### ❌ Error al conectar con la base de datos

        Hubo un problema al intentar establecer la conexión. Verifique los datos en su archivo `.env` y que el servidor sea accesible.

        **Detalle del error:**
        ```text
        {str(e)}
        ```
        """).callout(kind="danger")
        mo.stop(True, msg)

    # ==========================================================================
    # SINTAXIS DE RETORNO PARA VARIABLE ÚNICA
    # ==========================================================================
    # Al devolver una sola variable, DEBES usar una coma final: (var,)
    # Esto le dice a Python que es una tupla, no solo paréntesis de agrupación.
    # Sin la coma: (engine) es solo 'engine' con paréntesis.
    # Con la coma: (engine,) es una tupla que contiene a 'engine'.
    return (engine,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Selección de Tabla")

    # ==========================================================================
    # mo.ui - COMPONENTES DE INTERFAZ DE USUARIO DE MARIMO
    # ==========================================================================
    # mo.ui contiene todos los widgets interactivos. Son REACTIVOS: cuando el usuario
    # interactúa con ellos, ¡cualquier celda que dependa de ese widget se vuelve a ejecutar!
    #
    # mo.ui.dropdown() - Crea un menú desplegable
    # PARÁMETROS:
    #   options: lista de strings O dict {etiqueta: valor}
    #   value: valor seleccionado inicialmente
    #   label: etiqueta de texto que se muestra sobre el desplegable
    #
    # ACCESO AL VALOR:
    #   widget.value - devuelve el valor seleccionado actualmente
    #   ¡Este valor se actualiza automáticamente cuando el usuario hace una selección!
    table_selector = mo.ui.dropdown(
        options=["SentianceEventos", "MovDebug_Eventos"],
        value="MovDebug_Eventos",
        label="Select Source Table"
    )

    # ==========================================================================
    # MOSTRAR ELEMENTOS DE INTERFAZ
    # ==========================================================================
    # Solo referencia el widget como la última expresión para mostrarlo.
    # Se renderizará como un desplegable interactivo en la salida.
    table_selector
    return (table_selector,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Filtrado de Datos")

    # ==========================================================================
    # MÁS COMPONENTES DE INTERFAZ
    # ==========================================================================
    # mo.ui.text() - Entrada de texto de una sola línea
    #   label: texto de la etiqueta
    #   placeholder: sugerencia en gris que se muestra cuando está vacío
    #   value: valor inicial (opcional)
    sid_input = mo.ui.text(label="Sentiance ID", placeholder="Ingrese ID...")

    # ==========================================================================
    # mo.ui.run_button() - BOTÓN PARA EJECUTAR LA CONSULTA BAJO DEMANDA
    # ==========================================================================
    # A diferencia de los demás widgets, este NO dispara la consulta al cambiar
    # los filtros. La celda de consulta se detiene (mo.stop) hasta que el usuario
    # lo presiona. Esto evita cargar toda la base de datos al abrir la app.
    run_button = mo.ui.run_button(label="🔍 Buscar")

    # mo.ui.datetime() - Selector de fecha y hora
    #   label: texto de la etiqueta
    #   value: fecha/hora inicial (opcional)
    # start_dt = mo.ui.datetime(label="Start Date/Time")
    # end_dt = mo.ui.datetime(label="End Date/Time")
    import datetime
    start_dt = mo.ui.datetime(label="Start Date/Time", value=datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
    end_dt = mo.ui.datetime(label="End Date/Time", value=datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0))


    # ==========================================================================
    # mo.hstack() / mo.vstack() - COMPONENTES DE DISEÑO (LAYOUT)
    # ==========================================================================
    # mo.hstack() - Organiza elementos HORIZONTALMENTE (uno al lado del otro)
    # mo.vstack() - Organiza elementos VERTICALMENTE (apilados)
    #
    # PARÁMETROS:
    #   items: lista de elementos para organizar
    #   gap: espacio entre elementos (en unidades rem, ~16px)
    #   align: "start", "center", "end", "stretch"
    #   justify: "start", "center", "end", "space-between", "space-around"
    # El botón de búsqueda se apila DEBAJO del campo de Sentiance ID.
    filter_ui = mo.hstack(
        [mo.vstack([sid_input, run_button], gap=0.5), start_dt, end_dt],
        gap=2,
        align="start",
    )
    filter_ui
    return end_dt, run_button, sid_input, start_dt


@app.cell(hide_code=True)
def _(end_dt, engine, mo, run_button, sid_input, start_dt, table_selector):
    # ==========================================================================
    # COMPUERTA DE EJECUCIÓN - mo.stop()
    # ==========================================================================
    # Detiene esta celda (y todas las que dependen de ella) hasta que el usuario
    # presione el botón "Buscar". Así la app NO consulta la base al iniciarse.
    mo.stop(
        not run_button.value,
        mo.md("👆 *Configure los filtros y presione **🔍 Buscar** para ejecutar la consulta.*").callout(kind="info"),
    )

    # Construir consulta SQL dinámica (sin límite TOP: traemos todos los eventos
    # que coincidan con los filtros aplicados).
    base_query = f"SELECT * FROM VictaTMTK.dbo.{table_selector.value}"
    where_clauses = []

    # .value es cómo accedes al valor actual de CUALQUIER widget mo.ui
    sid = sid_input.value.strip() if sid_input.value else None
    start = start_dt.value if start_dt.value else None
    end = end_dt.value if end_dt.value else None

    if sid:
        where_clauses.append(f"sentianceid = '{sid}'")
    if start:
        where_clauses.append(f"fechahora >= '{start}'")
    if end:
        where_clauses.append(f"fechahora <= '{end}'")

    # ==========================================================================
    # GUARDA - BLOQUEAR ESCANEO COMPLETO SIN FILTROS
    # ==========================================================================
    # Sin límite TOP, una consulta sin ningún filtro traería toda la tabla.
    # Exigimos al menos un filtro (Sentiance ID o rango de fechas) antes de ejecutar.
    mo.stop(
        not where_clauses,
        mo.md(
            "⚠️ *Aplique al menos un filtro (**Sentiance ID** o un **rango de fechas**) "
            "antes de buscar. Una consulta sin filtros traería la tabla completa.*"
        ).callout(kind="warn"),
    )

    query = base_query
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY fechahora DESC"

    # ==========================================================================
    # mo.accordion() - SECCIONES DESPLEGABLES
    # ==========================================================================
    # Crea secciones que se pueden expandir o contraer.
    # Toma un dict: {título: contenido}
    query_log = mo.accordion({
        "📝 Log de Consulta SQL": mo.md(f"```sql\n{query}\n```")
    })

    # ==========================================================================
    # mo.sql() - EJECUCIÓN SQL INTEGRADA
    # ==========================================================================
    # ¡Marimo tiene soporte nativo para SQL! mo.sql() ejecuta consultas y devuelve un DataFrame.
    #
    # PARÁMETROS:
    #   query: cadena SQL para ejecutar
    #   output: si es True, muestra la tabla de resultados automáticamente
    #   engine: motor SQLAlchemy para la conexión a la base de datos
    #
    # Devuelve un pandas DataFrame con los resultados de la consulta.
    df = mo.sql(
        query,
        output=False,  # We'll display in our own table widget
        engine=engine
    )

    query_log  # Mostrar el acordeón
    return (df,)


@app.cell(hide_code=True)
def _(df, json):
    def _find_occupant_role(obj):
        # Re-parse string values — handles double-encoded JSON stored in SQL Server
        if isinstance(obj, str):
            stripped = obj.strip()
            if stripped.startswith(("{", "[")):
                try:
                    return _find_occupant_role(json.loads(stripped))
                except Exception:
                    pass
            return None
        if isinstance(obj, dict):
            if "occupantRole" in obj:
                return obj["occupantRole"]
            for v in obj.values():
                result = _find_occupant_role(v)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = _find_occupant_role(item)
                if result is not None:
                    return result
        return None

    def _extract_role(row):
        for col in row.index:
            val = row[col]
            if val is None:
                continue
            result = _find_occupant_role(val)
            if result is not None:
                return str(result)
        return None

    df_enriched = df.copy()
    # "category" dtype triggers marimo's value-frequency chips for this column
    # (marimo only shows summaries for categorical/numeric/temporal columns)
    roles = df_enriched.apply(_extract_role, axis=1).astype("category")

    # Case-insensitive search for the "Tipo" column
    tipo_col = next((c for c in df_enriched.columns if c.lower() == "tipo"), None)
    if tipo_col is not None:
        tipo_idx = df_enriched.columns.get_loc(tipo_col)
        df_enriched.insert(tipo_idx + 1, "Role", roles)
    else:
        df_enriched.insert(0, "Role", roles)
    return (df_enriched,)


@app.cell
def _(df_enriched, mo):
    # ==========================================================================
    # mo.ui.table() - TABLA DE DATOS INTERACTIVA
    # ==========================================================================
    # Renderiza un DataFrame como una tabla interactiva, ordenable y filtrable.
    #
    # PARÁMETROS:
    #   data: DataFrame o lista de diccionarios
    #   selection: "single" | "multi" | None
    #       - "single": el usuario puede seleccionar una fila
    #       - "multi": el usuario puede seleccionar múltiples filas
    #       - None: no se permite selección
    #   label: texto descriptivo
    #   page_size: filas por página (por defecto 10)
    #   pagination: True/False para habilitar paginación
    #
    # SELECCIÓN REACTIVA:
    #   table.value devuelve un DataFrame de la(s) fila(s) seleccionada(s)
    #   Cuando la selección cambia, ¡las celdas que usan table.value se vuelven a ejecutar!
    table = mo.ui.table(df_enriched, selection="single", label="Seleccione una fila para ver detalles")
    table
    return (table,)


@app.cell
def _(json, mo, table):
    # table.value es un DataFrame con las filas seleccionadas (vacío si no hay selección)
    selected_row = table.value

    if len(selected_row) > 0:
        row_data = selected_row.iloc[0]
        left_items = []
        right_items = []

        for col in row_data.index:
            val = row_data[col]
            is_json = False
            parsed = None

            try:
                if isinstance(val, str) and val.strip().startswith(("{", "[")):
                    parsed = json.loads(val)
                    is_json = True
                elif isinstance(val, (dict, list)):
                    parsed = val
                    is_json = True
            except:
                pass

            if is_json:
                field_ui = mo.vstack([
                    mo.md(f"**{col}**"),
                    mo.tree(parsed).style({"max-height": "800px", "overflow-y": "auto"})
                ], gap=0.5)
                right_items.append(field_ui)
            else:
                field_ui = mo.vstack([
                    mo.md(f"**{col}**"),
                    mo.ui.text_area(value=str(val), disabled=True, rows=2)
                ], gap=0.5)
                left_items.append(field_ui)

        # Diseño anidado: vstack dentro de hstack para diseños complejos
        view = mo.vstack([
            mo.md("### Detalle de Fila"),
            mo.hstack([
                mo.vstack(left_items, gap=1, align="stretch"),
                mo.vstack(right_items, gap=1, align="stretch")
            ], gap=2, align="start")
        ], gap=1)
    else:
        view = mo.md("💡 *Seleccione una fila en la tabla de arriba para ver sus detalles aquí.*")

    view  # Mostrar la vista construida
    return


@app.cell(hide_code=True)
def _(json, mo, pd, table):
    geo_selected_row = table.value

    if len(geo_selected_row) > 0:
        geo_row_data = geo_selected_row.iloc[0]
        geo_data_found = []

        def find_geo_structures(obj, parent_key="", in_path=False):
            """Busca recursivamente coordenadas o lat/long en dicts/lists"""
            if isinstance(obj, dict):
                current_is_path = False
                g_type = obj.get("type", obj.get("venue_type"))
                g_significance = obj.get("significance")
                g_accuracy = obj.get("accuracy")

                if "waypoints" in obj:
                    geo_data_found.append({
                        "Source": parent_key or "root",
                        "Kind": "Ruta 🛤️",
                        "GeoType": g_type,
                        "Significance": g_significance,
                        "Accuracy": g_accuracy,
                        "Summary": f"{len(obj['waypoints'])} waypoints found",
                        "Data": obj
                    })
                    current_is_path = True
                else:
                    coords = None
                    if "latitude" in obj and "longitude" in obj:
                        coords = (obj["latitude"], obj["longitude"])
                    elif isinstance(obj.get("location"), dict) and "latitude" in obj["location"] and "longitude" in obj["location"]:
                        coords = (obj["location"]["latitude"], obj["location"]["longitude"])
                        g_accuracy = g_accuracy or obj["location"].get("accuracy")

                    if coords and not in_path:
                        geo_data_found.append({
                            "Source": parent_key or "root",
                            "Kind": "Lugar 📍",
                            "GeoType": g_type,
                            "Significance": g_significance,
                            "Accuracy": g_accuracy,
                            "Summary": f"Coord: {coords[0]}, {coords[1]}",
                            "Data": obj,
                            "Lat": coords[0],
                            "Lon": coords[1]
                        })

                for k, v in obj.items():
                    find_geo_structures(v, f"{parent_key}.{k}" if parent_key else k, in_path=in_path or current_is_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_geo_structures(item, f"{parent_key}[{i}]", in_path=in_path)

        for geo_col in geo_row_data.index:
            geo_val = geo_row_data[geo_col]
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
            table_cols = ["Kind", "Source", "GeoType", "Significance", "Accuracy", "Summary"]
            table_cols = [c for c in table_cols if c in geo_df.columns]
            geo_table_ui = mo.ui.table(geo_df[table_cols], selection="single", label="Seleccione para hacer zoom en el mapa")
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
    if geo_table_ui is not None and geo_df is not None:
        if len(geo_table_ui.value) > 0:
            selected_item = geo_table_ui.value.iloc[0]
            orig_item = geo_df[geo_df["Source"] == selected_item["Source"]].iloc[0]

            if orig_item["Kind"] == "Lugar 📍":
                m = leafmap.Map(backend="ipyleaflet", center=[orig_item["Lat"], orig_item["Lon"]], zoom=15, minimize_control=True)
                m.add_marker(location=[orig_item["Lat"], orig_item["Lon"]], tooltip=f"{orig_item['Source']} - SELECCIONADO")
            elif orig_item["Kind"] == "Ruta 🛤️":
                pts = [[p["latitude"], p["longitude"]] for p in orig_item["Data"]["waypoints"]]
                if pts:
                    center_lat = sum(p[0] for p in pts) / len(pts)
                    center_lon = sum(p[1] for p in pts) / len(pts)
                    m = leafmap.Map(backend="ipyleaflet", center=[center_lat, center_lon], zoom=13, minimize_control=True)
                    coords = [[p["longitude"], p["latitude"]] for p in orig_item["Data"]["waypoints"]]
                    line_geojson = {
                        "type": "FeatureCollection",
                        "features": [{
                             "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": coords},
                            "properties": {"name": f"{orig_item['Source']} - SELECCIONADO"}
                        }]
                    }
                    m.add_geojson(line_geojson, layer_name=orig_item["Source"])
                else:
                    m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
            else:
                m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
        else:
            m = leafmap.Map(backend="ipyleaflet", center=[-34.6, -58.4], zoom=10, minimize_control=True)
            for idx, row in geo_df.iterrows():
                if row["Kind"] == "Lugar 📍":
                    m.add_marker(location=[row["Lat"], row["Lon"]], tooltip=f"{row['Source']} ({row['GeoType'] or ''})")
                elif row["Kind"] == "Ruta 🛤️":
                    coords = [[p["longitude"], p["latitude"]] for p in row["Data"]["waypoints"]]
                    if coords:
                        line_geojson = {
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": {"type": "LineString", "coordinates": coords},
                                "properties": {"name": row["Source"]}
                            }]
                        }
                        m.add_geojson(line_geojson, layer_name=row["Source"])

        geo_view = mo.vstack([
            mo.md("## 🌍 Vista Geográfica Interactiva"),
            mo.hstack([
                mo.vstack([mo.md("### Elementos"), geo_table_ui], align="stretch"),
                mo.vstack([mo.md("### Mapa"), m], align="stretch")
            ], gap=2, align="start"),
            mo.md("### Detalles"),
            mo.vstack([
                mo.vstack([
                    mo.md(f"#### {item['Kind']} (desde `{item['Source']}`)"),
                    mo.md(f"**Descripción:** {item['Summary']}"),
                    mo.accordion({"Datos Raw": mo.ui.text_area(value=json.dumps(item['Data'], indent=2), disabled=True, rows=10)})
                ], gap=0.5) for item in geo_data_found
            ], gap=2)
        ])
    else:
        geo_view = mo.md("ℹ️ *No se detectó información geográfica.*")

    geo_view
    return


if __name__ == "__main__":
    app.run()

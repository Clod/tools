"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           CONCILIACIÓN DEL REGISTRO DE DIAGNÓSTICO - MARIMO                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ QUÉ HACE ESTE NOTEBOOK                                                       ║
║ Compara lo que los teléfonos DICEN haber entregado al backend contra lo que  ║
║ efectivamente quedó guardado en la tabla SentianceEventos.                   ║
║                                                                              ║
║ Arriba muestra un barrido de la flota: un renglón por dispositivo. Al        ║
║ seleccionar un renglón se despliega el detalle de ese dispositivo.           ║
║                                                                              ║
║ CÓMO EJECUTARLO                                                              ║
║                                                                              ║
║ 1. MODO EDICIÓN (se ve y se edita el código):                                ║
║    $ uv run marimo edit conciliacion_registro.py                             ║
║                                                                              ║
║ 2. MODO APLICACIÓN (solo la interfaz, sin código a la vista):                ║
║    $ uv run marimo run conciliacion_registro.py                              ║
║                                                                              ║
║ Necesita un archivo .env en este mismo directorio con DB_SERVER, DB_NAME,    ║
║ DB_USER, DB_PASS y opcionalmente DB_PORT.                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# =============================================================================
# DECLARACIÓN DE DEPENDENCIAS PARA UV
# =============================================================================
# Este bloque de comentarios no es decorativo: es un estándar de Python (PEP 723)
# que `uv` lee para instalar lo necesario antes de ejecutar. Por eso alcanza con
# `uv run marimo edit ...` sin instalar nada a mano.
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "sqlalchemy",
#     "pymssql",
#     "python-dotenv",
# ]
# ///

import marimo

__generated_with = "0.23.8"

# `width="full"` hace que el contenido ocupe todo el ancho de la ventana. Sirve
# acá porque las tablas tienen varias columnas.
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _():
    # =========================================================================
    # LAS IMPORTACIONES VAN DENTRO DE UNA CELDA, Y SE DEVUELVEN
    # =========================================================================
    # En marimo cada celda es una unidad que declara qué necesita (sus
    # parámetros) y qué ofrece (lo que devuelve). El orden de ejecución no lo da
    # la posición en el archivo, lo da esa dependencia entre celdas.
    #
    # Por eso las importaciones se hacen acá adentro y se devuelven: si se
    # hicieran a nivel de módulo, marimo no podría saber qué celda usa qué, y no
    # sabría cuáles re-ejecutar cuando algo cambia.
    import marimo as mo
    import pandas as pd
    import sqlalchemy
    import os
    import datetime
    from dotenv import load_dotenv

    # El resultado se asigna a `_` para que no se muestre. En marimo la ÚLTIMA
    # expresión de una celda se renderiza como salida; `load_dotenv()` devuelve
    # True y sin esta asignación aparecería un "True" suelto arriba de todo.
    _ = load_dotenv()

    # =========================================================================
    # LA SENTENCIA RETURN ES LO QUE EXPORTA
    # =========================================================================
    # Solo lo que se devuelve queda disponible para otras celdas, y aparece como
    # PARÁMETRO en la firma de las que lo usan. Con una sola variable hay que
    # poner la coma final: `return (engine,)`, no `return (engine)`.
    return datetime, mo, os, pd, sqlalchemy


@app.cell(hide_code=True)
def _(mo):
    # mo.md() convierte texto markdown en salida formateada. Al ser la última
    # expresión de la celda, se muestra sin necesidad de print().
    mo.md(
        """
        # Conciliación del registro de diagnóstico

        Compara lo que los teléfonos **dicen** haber entregado contra lo que
        **quedó guardado** en la base.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Qué se está conciliando

        La app escribe un **registro de diagnóstico** en el propio teléfono: una
        línea por cada cosa que ocurre adentro. Cada tanto ese archivo se manda
        al backend como una fila más de `SentianceEventos`, con `tipo` igual a
        `AuditLogBatch`, y con todas sus líneas adentro del campo `json`.

        O sea que en esa tabla conviven dos cosas distintas:

        - **Los eventos de telemetría**: un viaje, un choque, un cambio de
          contexto. Una fila por evento.
        - **El registro de diagnóstico**: filas que contienen, cada una, decenas
          o cientos de líneas que describen lo que el teléfono hizo.

        Conciliar es cruzar las dos. Si el registro dice "entregué este viaje" y
        no hay fila de viaje, algo se perdió entre el teléfono y la base.

        ### Las fases de una línea del registro

        Cada línea tiene una `fase` que dice en qué momento del recorrido está
        el evento:

        | Fase | Quién escribe la línea | Significa |
        |---|---|---|
        | `RX` | la fachada | La fachada recibió el evento del SDK de Sentiance. |
        | `RX_APP` | la app | La app recibió de la fachada **ese mismo evento**. |
        | `TX_IN` | el cliente de eventos | El cliente de eventos tomó el evento para enviarlo. |
        | `TX_OK` | el cliente de eventos | El backend confirmó que lo recibió. |
        | `TX_FAIL` | el cliente de eventos | El envío falló y el evento quedó en la cola. |
        | `TX_DROP` | el cliente de eventos | El evento se descartó sin entregarse. |
        | `FLUSH_START` / `FLUSH_END` | el cliente de eventos | Ciclo de vaciado de la cola. |

        ### Por qué un evento recibido escribe dos líneas

        `RX` y `RX_APP` describen la misma recepción anotada dos veces, y las
        dos líneas existen a propósito.

        Un evento del SDK de Sentiance llega primero a la fachada
        `@victa/telematics-facade`, que escribe `RX`. La fachada se lo pasa
        entonces al manejador que la app registró, y ese manejador escribe
        `RX_APP` antes de mandar el evento. El primer emisor es la librería, el
        segundo es `src/services/telematics.ts` de la app.

        La consecuencia práctica: **contar `RX` y `RX_APP` juntas da el doble de
        eventos recibidos que los eventos recibidos reales.** Hay que contar una
        sola de las dos.

        Hasta el 2026-09-05 las dos líneas usaban la fase `RX`, y para
        distinguirlas había que mirar si la línea traía o no el campo `ts`. Los
        registros anteriores a esa fecha siguen necesitando ese criterio.

        La conciliación se apoya en `TX_OK`: es la declaración de entrega, y a
        cada una debería corresponderle una fila guardada.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo, os, sqlalchemy):
    # =========================================================================
    # CONEXIÓN, Y mo.stop() COMO COMPUERTA
    # =========================================================================
    # mo.stop(condicion, salida) detiene esta celda si la condición es verdadera,
    # muestra `salida` en su lugar, y deja sin ejecutar a TODAS las celdas que
    # dependan de lo que esta iba a devolver. Es la forma de manejar
    # precondiciones en marimo: no hace falta envolver todo en un if gigante.
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    port = os.getenv("DB_PORT", "9433")

    faltantes = [
        nombre
        for nombre, valor in {
            "DB_SERVER": server,
            "DB_NAME": database,
            "DB_USER": username,
            "DB_PASS": password,
        }.items()
        if not valor
    ]

    if faltantes:
        # .callout(kind=...) enmarca el markdown en un recuadro de color.
        # Los tipos son "info", "success", "warn", "danger" y "neutral".
        mo.stop(
            True,
            mo.md(
                f"""
                ### Configuración incompleta

                Falta definir en el archivo `.env`: {", ".join(f"`{f}`" for f in faltantes)}
                """
            ).callout(kind="warn"),
        )

    try:
        # mo.status.spinner() muestra un indicador mientras dura el bloque.
        with mo.status.spinner(title="Conectando con la base de datos..."):
            engine = sqlalchemy.create_engine(
                f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"
            )
            # Abrir y cerrar una conexión valida las credenciales ahora, y no
            # más tarde en medio de una consulta.
            with engine.connect() as _conn:
                pass
    except Exception as e:
        mo.stop(
            True,
            mo.md(
                f"""
                ### Error al conectar

                ```text
                {e}
                ```
                """
            ).callout(kind="danger"),
        )

    return (engine,)


@app.cell(hide_code=True)
def _(datetime, mo):
    # =========================================================================
    # UNA PREOCUPACIÓN POR CELDA
    # =========================================================================
    # Marimo re-ejecuta la celda ENTERA cada vez que se interactúa con
    # cualquiera de los controles que ella define. Si el rango de fechas, el
    # botón y la tabla de resultados vivieran juntos, elegir una fecha
    # reconstruiría la tabla y borraría la selección de dispositivo.
    #
    # Por eso los controles de filtrado están solos acá, y la tabla vive en su
    # propia celda más abajo.
    #
    # mo.ui.datetime() es un selector de fecha y hora. mo.ui.run_button() es un
    # botón cuyo `.value` vale True únicamente durante la ejecución que dispara
    # el clic. Sirve para que una consulta pesada no se lance sola al abrir la
    # aplicación ni cada vez que se toca una fecha.
    #
    # Las fechas se escriben explícitas a propósito. El reloj del servidor de
    # base de datos está corrido respecto de las fechas guardadas en la columna
    # `fechahora`, así que un filtro relativo con GETDATE() puede devolver cero
    # filas aunque los datos estén ahí.
    _hoy = datetime.datetime.now()
    desde = mo.ui.datetime(
        label="Desde",
        value=(_hoy - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
    )
    hasta = mo.ui.datetime(
        label="Hasta",
        value=_hoy.replace(hour=23, minute=59, second=59, microsecond=0),
    )
    buscar = mo.ui.run_button(label="Conciliar")

    # mo.hstack() acomoda los elementos en horizontal; mo.vstack() en vertical.
    mo.hstack([desde, hasta, buscar], gap=2, align="end")
    return buscar, desde, hasta


@app.cell(hide_code=True)
def _(buscar, desde, engine, hasta, mo, pd):
    # =========================================================================
    # LA CONSULTA: DOS MITADES QUE DESPUÉS SE CRUZAN
    # =========================================================================
    # Esta celda no corre hasta que se aprieta el botón. Mientras tanto muestra
    # el mensaje y deja detenidas a todas las celdas que dependen de `detalle`.
    mo.stop(not buscar.value, mo.md("Elegí un rango y apretá **Conciliar**."))

    # ESTA ES LA ÚNICA CELDA QUE MIRA `buscar`, Y TIENE QUE SEGUIR SIÉNDOLO
    # ---------------------------------------------------------------------
    # `mo.ui.run_button()` vuelve a `value = False` una vez que corrieron las
    # celdas que el botón disparó. Una celda de aguas abajo que se re-ejecute
    # más tarde —por ejemplo al elegir un dispositivo en la tabla de la flota—
    # va a leer `buscar.value` como False y detenerse sin dibujar nada.
    #
    # Las celdas de aguas abajo no necesitan la compuerta: dependen de
    # `detalle` o de `sid`, y esos nombres no existen hasta que esta celda
    # corre. El grafo de marimo ya las mantiene detenidas.
    #
    # Medido el 2026-09-09: con `mo.stop(not buscar.value)` en las tres celdas
    # finales, apretar Conciliar y después elegir un dispositivo dejaba la
    # página cortada en el detalle por tipo, sin mensaje ni error.

    _desde = desde.value.strftime("%Y-%m-%d %H:%M:%S")
    _hasta = hasta.value.strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    # MITAD 1 - LO DECLARADO: las entregas que el teléfono anotó en su registro.
    # -------------------------------------------------------------------------
    # El registro viaja dentro del campo `json`, en un arreglo llamado `lineas`.
    # OPENJSON con CROSS APPLY lo abre y devuelve una fila de SQL por cada línea
    # del registro, como si fuera una tabla.
    #
    # Se expande en SQL y no en pandas por tamaño: un solo lote puede pesar
    # cientos de kilobytes, y traerlo entero para desarmarlo en Python sería caro
    # sin necesidad.
    #
    # TRES DECISIONES EN ESTA CONSULTA, CADA UNA CON SU MOTIVO:
    #
    # 1. Se filtra por `entry.ts`, la marca de tiempo que pone la librería en
    #    cada línea, y NO por la fecha de la fila del lote. Un lote entregado a
    #    las 10:00 puede contener líneas escritas a las 08:00, porque el archivo
    #    se acumula en el teléfono antes de mandarse. Filtrar por la fila
    #    correría todo el análisis.
    #
    # 2. Se excluyen los tipos `AuditLogBatch` y `-`. El primero es el traslado
    #    del propio registro: mandar el registro genera líneas sobre ese envío.
    #    El segundo son ciclos de vaciado de cola que no pertenecen a ningún
    #    evento. Ninguno de los dos es telemetría.
    #
    # 3. Solo interesan las líneas con fase `TX_OK`, que son las entregas que el
    #    backend confirmó.
    _sql_declarado = f"""
        SELECT e.sentianceid,
               JSON_VALUE(l.value,'$.entry.tipo') AS tipo,
               COUNT(*) AS declaradas
        FROM SentianceEventos e
        CROSS APPLY OPENJSON(e.json,'$.lineas') l
        WHERE e.tipo = 'AuditLogBatch'
          AND JSON_VALUE(l.value,'$.entry.fase') = 'TX_OK'
          AND JSON_VALUE(l.value,'$.entry.tipo') NOT IN ('AuditLogBatch','-')
          AND JSON_VALUE(l.value,'$.entry.ts') >= '{_desde}'
          AND JSON_VALUE(l.value,'$.entry.ts') <= '{_hasta}'
        GROUP BY e.sentianceid, JSON_VALUE(l.value,'$.entry.tipo')
    """

    # -------------------------------------------------------------------------
    # MITAD 2 - LO GUARDADO: las filas que realmente quedaron en la tabla.
    # -------------------------------------------------------------------------
    # Se excluye `SDKStatus`. Esas filas las manda `victaService.ts` con su
    # propio `fetch`, sin pasar por el cliente de eventos, así que por
    # construcción nunca tienen una entrega declarada en el registro. Incluirlas
    # mostraría una discrepancia permanente que no es tal.
    _sql_guardado = f"""
        SELECT sentianceid, tipo, COUNT(*) AS guardadas
        FROM SentianceEventos
        WHERE tipo NOT IN ('AuditLogBatch','SDKStatus')
          AND fechahora >= '{_desde}'
          AND fechahora <= '{_hasta}'
        GROUP BY sentianceid, tipo
    """

    with mo.status.spinner(title="Conciliando..."):
        _declarado = pd.read_sql(_sql_declarado, engine)
        _guardado = pd.read_sql(_sql_guardado, engine)

    # -------------------------------------------------------------------------
    # EL CRUCE
    # -------------------------------------------------------------------------
    # Unión externa, no interna: interesan las dos direcciones. Una entrega
    # declarada sin fila guardada es una pérdida. Una fila guardada sin entrega
    # declarada también es un hallazgo, aunque distinto: significa que llegó algo
    # que el registro no menciona.
    detalle = _declarado.merge(_guardado, on=["sentianceid", "tipo"], how="outer")
    detalle[["declaradas", "guardadas"]] = detalle[["declaradas", "guardadas"]].fillna(0).astype(int)
    detalle["diferencia"] = detalle["declaradas"] - detalle["guardadas"]

    # Solo los dispositivos que mandaron registro en el período. Un teléfono con
    # una versión vieja de la app, o de otro producto, no tiene nada que
    # conciliar: sus filas guardadas contra cero declaraciones darían una
    # diferencia enorme que no significa pérdida.
    #
    # Medido el 2026-09-08: sin este filtro, los ocho primeros del barrido eran
    # todos de ese tipo, con diferencias de hasta 255, y tapaban a los cuatro
    # dispositivos que sí había que mirar.
    _con_registro = set(_declarado["sentianceid"])
    detalle = detalle[detalle["sentianceid"].isin(_con_registro)].reset_index(drop=True)
    return (detalle,)


@app.cell(hide_code=True)
def _(detalle, mo):
    # =========================================================================
    # EL BARRIDO DE LA FLOTA, Y UNA TABLA QUE ALIMENTA OTRAS CELDAS
    # =========================================================================
    # mo.ui.table(..., selection="single") dibuja una tabla donde se puede
    # seleccionar un renglón. Su `.value` es un DataFrame con los renglones
    # seleccionados, y otras celdas pueden depender de él: al elegir un renglón,
    # esas celdas se re-ejecutan solas.
    #
    # Esa es la reactividad de marimo. No hay que escribir ningún manejador de
    # eventos ni volver a dibujar nada: alcanza con que la celda de destino
    # reciba `tabla_flota` como parámetro.
    resumen = (
        detalle.groupby("sentianceid", as_index=False)
        .agg(
            declaradas=("declaradas", "sum"),
            guardadas=("guardadas", "sum"),
            tipos=("tipo", "nunique"),
        )
        .assign(diferencia=lambda d: d["declaradas"] - d["guardadas"])
        # Se ordena por valor absoluto de la diferencia: interesan tanto las
        # entregas sin fila como las filas sin entrega.
        .sort_values("diferencia", key=abs, ascending=False)
        .reset_index(drop=True)
    )

    mo.stop(
        resumen.empty,
        mo.md("No hay datos en ese rango.").callout(kind="warn"),
    )

    # Acá había un recuadro que contaba cuántos dispositivos no cuadraban.
    # Se sacó porque contaba siempre lo mismo: casi ningún dispositivo cuadra,
    # y no porque haya pérdidas. Una diferencia distinta de cero es el estado
    # normal, ya que basta con que un archivo del registro siga abierto en el
    # teléfono para que falten líneas, o con que un evento haya quedado
    # atribuido a otro usuario para que sobre de un lado y falte del otro.
    #
    # Un recuento que sí valdría la pena es el de pérdidas ciertas: entregas
    # declaradas con TX_OK sin fila bajo ningún sentianceid. Ese dato no se
    # puede sacar de esta tabla, porque exige el apareo evento por evento que
    # hace la celda "Diferencias, una por una" para un solo dispositivo.

    # El nombre interno de la columna sigue siendo `declaradas`, porque es el
    # que usan el cruce y el cálculo de la diferencia. Solo se cambia la
    # etiqueta que ve quien lee la tabla: "declaradas" sola no dice de dónde
    # sale el número, y sale del registro que mandó el teléfono.
    #
    # El renombre va acá y no en la consulta a propósito. `tabla_flota.value`
    # devuelve las filas seleccionadas con estos nombres, y la celda de aguas
    # abajo solo lee de ahí la columna `sentianceid`, que no cambia.
    tabla_flota = mo.ui.table(
        resumen.rename(columns={"declaradas": "declaradas en logs"}),
        selection="single",
        label="Dispositivos",
    )
    tabla_flota
    return (tabla_flota,)


@app.cell(hide_code=True)
def _(detalle, mo, tabla_flota):
    # =========================================================================
    # DETALLE POR TIPO DE EVENTO
    # =========================================================================
    # Esta celda depende de `tabla_flota`, así que marimo la vuelve a ejecutar
    # cada vez que cambia la selección. Está separada de la celda de la consulta
    # a propósito: elegir un dispositivo no vuelve a golpear la base de datos.
    #
    # Esta tabla da la diferencia por tipo de evento, que es un número. El
    # número no dice si hay que investigar: la celda siguiente descompone cada
    # diferencia en el evento concreto que la produjo y en su causa.
    _sel = tabla_flota.value
    mo.stop(
        _sel is None or len(_sel) == 0,
        mo.md("Elegí un dispositivo de la tabla para ver el detalle."),
    )

    sid = _sel.iloc[0]["sentianceid"]

    _por_tipo = (
        detalle[detalle["sentianceid"] == sid][["tipo", "declaradas", "guardadas", "diferencia"]]
        .sort_values("tipo")
        .reset_index(drop=True)
    )

    mo.vstack(
        [
            mo.md(f"### Entregas declaradas contra filas guardadas — `{sid}`"),
            mo.ui.table(
                _por_tipo.rename(columns={"declaradas": "declaradas en logs"}),
                selection=None,
            ),
        ]
    )
    return (sid,)


@app.cell(hide_code=True)
def _(desde, engine, hasta, mo, pd, sid):
    # =========================================================================
    # LAS DIFERENCIAS, UNA POR UNA, Y POR QUÉ EXISTE CADA UNA
    # =========================================================================
    # La tabla de la flota dice CUÁNTAS diferencias tiene un dispositivo. Un
    # número solo no alcanza para decidir si hay que investigar: una diferencia
    # de 2 puede ser una pérdida de dos eventos o puede no ser una pérdida en
    # absoluto. Esta celda muestra CUÁL es cada diferencia, a qué hora ocurrió,
    # y a cuál de tres causas corresponde.
    #
    # CÓMO SE APAREJAN LAS DOS MITADES
    # --------------------------------
    # Entre una línea del registro y una fila de la tabla no hay ninguna clave
    # en común. El apareo es por tipo de evento y cercanía en el tiempo: para
    # cada entrega declarada se busca la fila del mismo tipo más próxima, y
    # cada fila se consume una sola vez. Lo que queda sin pareja es la
    # diferencia.
    #
    # La tolerancia es de 5 segundos. La columna `fechahora` de la tabla guarda
    # segundos enteros mientras que `entry.ts` del registro guarda milésimas,
    # así que aun para el mismo evento las dos marcas de tiempo difieren.
    #
    # LAS TRES CAUSAS, COMPROBADAS SOBRE ESTOS DATOS EL 2026-09-08
    # -----------------------------------------------------------
    # 1. LA FILA QUEDÓ BAJO OTRO USUARIO. El par existe, con el mismo tipo y la
    #    misma hora, pero guardado contra otro sentianceid. El dispositivo
    #    6aa061750c376556e45ffee4 declaró dos TimelineUpdate entregados a las
    #    16:29:45 y 16:29:46, y las dos filas correspondientes quedaron bajo
    #    6a84c653be6f21eb61645396. Esa es la firma del problema de atribución
    #    al cambiar de usuario: el evento se encoló con un identificador y se
    #    entregó con el otro. Aparece como faltante en un dispositivo y como
    #    sobrante en el otro, así que suma dos diferencias por cada evento.
    #
    # 2. PUEDE ESTAR EN CAMINO TODAVÍA. El par no aparece, y el evento ocurrió
    #    dentro de los últimos 15 minutos. El envío del registro de auditoría
    #    no es inmediato: un archivo se cierra al llegar a su tamaño de corte,
    #    espera diez minutos sin escrituras, y recién entonces entra en un
    #    ciclo que manda hasta cinco archivos cada cinco minutos y solo con red
    #    disponible. Volver a conciliar más tarde resuelve estas diferencias.
    #
    # 3. EL PAR NO APARECE BAJO NINGÚN USUARIO. La otra mitad no está en ningún
    #    dispositivo del período, así que ya quedó descartada la atribución
    #    cruzada de la causa 1. Qué significa depende de cuál mitad falta:
    #
    #    - Falta la línea TX_OK del registro. El evento llegó, lo que no llegó
    #      es el archivo que lo declara. La causa 2 solo cubre 15 minutos, pero
    #      un archivo puede tardar mucho más, así que todavía no es una
    #      pérdida: se espera, o se toca "Enviar Audit Log ahora" en la
    #      pantalla de perfil, que cierra el archivo en curso y lo manda sin
    #      esperar los diez minutos de quietud.
    #
    #    - Falta la fila en la base. Acá no hay nada que esperar. TX_OK
    #      significa que el backend confirmó la recepción, así que la fila
    #      debería existir. El dispositivo 6aa018266101ed3419e633eb declaró 17
    #      entregas confirmadas —un SDKReset y dieciséis VehicleCrash entre las
    #      13:30 y las 14:14 del 2026-09-08— y ninguna de las 17 tiene fila
    #      bajo ningún sentianceid. Eso es una pérdida.

    _desde = desde.value.strftime("%Y-%m-%d %H:%M:%S")
    _hasta = hasta.value.strftime("%Y-%m-%d %H:%M:%S")
    _TOLERANCIA = pd.Timedelta(seconds=5)
    # Hace cuánto tiene que haber ocurrido un evento para que su ausencia
    # todavía no signifique nada. Diez minutos es el tiempo de quietud que
    # espera el envío del registro; se toman quince para dejar margen.
    #
    # Es un piso muy bajo, no un plazo. Un archivo se cierra al llegar a
    # 512 KB, al morir el motor de JavaScript, o al tocar "Enviar Audit Log
    # ahora"; en un teléfono con poca actividad puede quedar abierto durante
    # horas, y hasta que no se cierra no se manda. O sea que pasados los quince
    # minutos la ausencia de una línea del registro sigue sin significar
    # pérdida. Por eso la causa que sigue en la clasificación no afirma que
    # haya una pérdida, sino que separa por cuál mitad falta.
    _EN_VUELO = pd.Timedelta(minutes=15)

    # Las dos consultas traen TODOS los dispositivos, no solo el seleccionado.
    # Sin las filas de los demás no se puede detectar la causa 1, que consiste
    # justamente en que el par está bajo otro sentianceid.
    _declaraciones = pd.read_sql(f"""
        SELECT e.sentianceid AS sid,
               JSON_VALUE(l.value,'$.entry.tipo') AS tipo,
               JSON_VALUE(l.value,'$.entry.ts') AS momento
        FROM SentianceEventos e
        CROSS APPLY OPENJSON(e.json,'$.lineas') l
        WHERE e.tipo = 'AuditLogBatch'
          AND JSON_VALUE(l.value,'$.entry.fase') = 'TX_OK'
          AND JSON_VALUE(l.value,'$.entry.tipo') NOT IN ('AuditLogBatch','-')
          AND JSON_VALUE(l.value,'$.entry.ts') >= '{_desde}'
          AND JSON_VALUE(l.value,'$.entry.ts') <= '{_hasta}'
    """, engine)

    _filas = pd.read_sql(f"""
        SELECT sentianceid AS sid, tipo, fechahora AS momento
        FROM SentianceEventos
        WHERE tipo NOT IN ('AuditLogBatch','SDKStatus')
          AND fechahora >= '{_desde}'
          AND fechahora <= '{_hasta}'
    """, engine)

    for _df in (_declaraciones, _filas):
        _df["momento"] = pd.to_datetime(_df["momento"])

    def _sin_pareja(izq, der):
        """Devuelve las marcas de tiempo de `izq` que no encontraron pareja
        en `der`, y las de `der` que quedaron libres. Apareo codicioso: se
        recorre `izq` en orden y cada elemento toma el más cercano disponible.
        """
        libres = sorted(der)
        huerfanas = []
        for _m in sorted(izq):
            _cerca = [x for x in libres if abs(x - _m) <= _TOLERANCIA]
            if _cerca:
                libres.remove(min(_cerca, key=lambda x: abs(x - _m)))
            else:
                huerfanas.append(_m)
        return huerfanas, libres

    _d_sid = _declaraciones[_declaraciones["sid"] == sid]
    _f_sid = _filas[_filas["sid"] == sid]

    _sueltas = []
    for _tipo in sorted(set(_d_sid["tipo"]) | set(_f_sid["tipo"])):
        _decl_solas, _filas_solas = _sin_pareja(
            _d_sid[_d_sid["tipo"] == _tipo]["momento"],
            _f_sid[_f_sid["tipo"] == _tipo]["momento"],
        )
        # Para cada huérfana se busca su par bajo CUALQUIER otro sentianceid.
        _otras_filas = _filas[(_filas["tipo"] == _tipo) & (_filas["sid"] != sid)]
        for _m in _decl_solas:
            _par = _otras_filas[(_otras_filas["momento"] - _m).abs() <= _TOLERANCIA]
            _sueltas.append({
                "tipo": _tipo,
                "momento": _m,
                "falta": "la fila en la base",
                "otro_usuario": _par.iloc[0]["sid"] if len(_par) else None,
            })
        _otras_decl = _declaraciones[(_declaraciones["tipo"] == _tipo) & (_declaraciones["sid"] != sid)]
        for _m in _filas_solas:
            _par = _otras_decl[(_otras_decl["momento"] - _m).abs() <= _TOLERANCIA]
            _sueltas.append({
                "tipo": _tipo,
                "momento": _m,
                "falta": "la línea TX_OK del registro",
                "otro_usuario": _par.iloc[0]["sid"] if len(_par) else None,
            })

    sueltas = pd.DataFrame(_sueltas)

    if len(sueltas):
        # El corte se mide SIEMPRE contra el presente, y nunca contra el fin
        # del rango elegido. Lo que decide si algo puede seguir en camino es
        # cuánto tiempo pasó desde que ocurrió el evento hasta ahora, y eso no
        # depende de qué rango se haya pedido. Con un rango que termina ayer,
        # ningún evento califica: los archivos del registro tuvieron toda la
        # noche para llegar, así que su ausencia ya es un dato y no una espera.
        _corte = pd.Timestamp.now() - _EN_VUELO

        def _causa(fila):
            if fila["otro_usuario"]:
                return "el par quedó bajo otro usuario"
            if fila["momento"] >= _corte:
                return "puede estar en camino todavía"
            return "el par no aparece bajo ningún usuario"

        sueltas["causa"] = sueltas.apply(_causa, axis=1)
        sueltas = sueltas.sort_values("momento").reset_index(drop=True)
        sueltas = sueltas[["momento", "tipo", "falta", "causa", "otro_usuario"]]

        # El recuadro se pinta en rojo solo por las pérdidas ciertas, que son
        # los eventos con entrega declarada y sin fila. Un evento al que le
        # falta la línea del registro no es una pérdida: el archivo puede
        # seguir en el teléfono, y forzar el envío lo trae.
        _cuenta = sueltas["causa"].value_counts()
        _perdidas = int(
            (
                (sueltas["causa"] == "el par no aparece bajo ningún usuario")
                & (sueltas["falta"] == "la fila en la base")
            ).sum()
        )
        _resumen = mo.md(
            "\n".join(
                [f"**{len(sueltas)} evento(s) sin pareja:**", ""]
                + [f"- {_n} — {_c}" for _c, _n in _cuenta.items()]
            )
        ).callout(kind="danger" if _perdidas else "warn")
        # Igual que en la tabla de la flota, el nombre interno se conserva
        # —`momento` es el que usan el ordenamiento y la clasificación— y solo
        # se cambia la etiqueta. "momento" solo no dice momento de qué.
        _detalle = mo.ui.table(
            sueltas.rename(columns={"momento": "hora del evento"}),
            selection=None,
        )
    else:
        _resumen = mo.md(
            "**Todo apareado: cada entrega declarada tiene su fila y cada fila su declaración.**"
        ).callout(kind="success")
        _detalle = mo.md("")

    mo.vstack(
        [
            mo.md("### Diferencias, una por una"),
            mo.md(
                """
                La tabla anterior da la diferencia como un número por tipo de
                evento. Acá esa diferencia se abre: **un renglón por cada
                evento que la produjo**.

                Abrirla exige aparear las dos mitades. Entre una línea del
                registro y una fila de la base no hay ninguna clave en común,
                así que el apareo es por tipo de evento y cercanía en el
                tiempo, con una tolerancia de 5 segundos. La tolerancia es
                necesaria porque la columna `fechahora` de la base guarda
                segundos enteros y el campo `entry.ts` del registro guarda
                milésimas, de modo que las dos marcas de tiempo de un mismo
                evento nunca coinciden exactamente. Cada fila de la base se
                aparea una sola vez.

                Los eventos que quedan sin pareja son la diferencia. La columna
                `hora del evento` es la marca de tiempo de la mitad que sí
                apareció: el campo `entry.ts` de la línea del registro cuando
                la que falta es la fila, y la columna `fechahora` de la fila
                cuando la que falta es la línea.

                La columna `falta` dice cuál de las dos mitades es la que no apareció, y
                toma uno de dos valores: `la fila en la base` cuando el
                registro declaró la entrega y no hay fila en `SentianceEventos`,
                o `la línea TX_OK del registro` cuando la fila existe y ningún
                lote recibido trae la línea que la declara.

                La columna `causa` dice por qué, y es la que separa las
                diferencias que hay que investigar de las que se explican
                solas:

                | Causa | Qué significa | Qué hacer |
                |---|---|---|
                | **el par quedó bajo otro usuario** | El evento existe de los dos lados, pero el registro lo declara bajo un `sentianceid` y la base lo guardó bajo otro. La columna `otro_usuario` trae el identificador del otro lado. | Es atribución cruzada al cambiar de usuario. Suma dos diferencias por evento: falta en un dispositivo y sobra en el otro. |
                | **puede estar en camino todavía** | El evento ocurrió hace menos de 15 minutos, contados desde este momento. Demasiado reciente para mirarlo. | Esperar y volver a conciliar más tarde. Si hace falta la respuesta ya, pedirle a la persona que toque **Enviar Audit Log ahora** en la pantalla de perfil, y conciliar de nuevo: eso cierra el archivo en curso y lo manda enseguida. |
                | **el par no aparece bajo ningún usuario** | La otra mitad no está: ni bajo este `sentianceid` ni bajo ningún otro dispositivo dentro del rango **Desde – Hasta**. La búsqueda ya recorrió todos los dispositivos, así que no es atribución cruzada. | Depende de qué falta. Ver abajo. |

                Los 15 minutos no son un plazo que al vencerse convierta la
                ausencia en pérdida. Un archivo del registro se cierra solo al
                llegar a 512 KB, o cuando muere el motor de JavaScript de la
                app, o cuando alguien toca **Enviar Audit Log ahora**. En un
                teléfono con poca actividad ese archivo puede quedar abierto
                durante horas, y hasta que no se cierra no se manda. Por eso un
                evento de ayer sin su línea del registro tampoco está perdido:
                cae en la causa siguiente, que separa según cuál mitad falta y
                tampoco afirma que haya pérdida.

                En los dos casos, el de hace quince minutos y el de ayer, hay
                una salida más rápida que esperar: pedirle a la persona que
                toque **Enviar Audit Log ahora** en la pantalla de perfil, y
                volver a conciliar. Ese botón cierra el archivo en curso y lo
                manda enseguida, así que una diferencia que era solo un archivo
                sin cerrar desaparece en la conciliación siguiente. La que no
                desaparece después de forzar el envío es la que hay que mirar.

                ### Qué hacer cuando el par no aparece bajo ningún usuario

                Lo que corresponde hacer depende de cuál de las dos mitades es
                la que falta, y las dos situaciones no se parecen en nada.

                **Falta `la línea TX_OK del registro`.** La fila está en la
                base, así que el evento llegó. Lo que no llegó es el archivo
                del registro que lo declara, y ese archivo puede seguir en el
                teléfono. La causa `puede estar en camino todavía` solo cubre
                los últimos 15 minutos, pero un archivo puede tardar mucho más:
                se cierra al llegar a su tamaño de corte, espera diez minutos
                sin escrituras, y recién entonces entra en un ciclo de envío
                que manda hasta cinco archivos cada cinco minutos y solo con
                red disponible. Antes de dar nada por perdido hay dos caminos:

                - Esperar y volver a conciliar más tarde.
                - Pedirle a la persona que abra la pantalla de perfil y toque
                  **Enviar Audit Log ahora**. Ese botón cierra el archivo que
                  se está escribiendo y lo manda enseguida, sin esperar los
                  diez minutos de quietud.

                **Falta `la fila en la base`.** Acá no hay nada que esperar. La
                línea `TX_OK` significa que el backend confirmó la recepción
                del evento, así que la fila debería existir y no existe. Esta
                es la única situación de las que muestra la tabla que indica
                una pérdida, y hay que investigarla.
                """
            ),
            _resumen,
            _detalle,
        ]
    )
    return


@app.cell(hide_code=True)
def _(engine, mo, pd, sid):
    # =========================================================================
    # RECEPCIÓN CONTRA ENTREGA, DENTRO DEL PROPIO REGISTRO
    # =========================================================================
    # La comparación anterior mira hacia afuera: lo declarado contra la base.
    # Esta mira hacia adentro del registro, y detecta un hueco que la otra no
    # puede ver.
    #
    # Si el SDK entregó un evento a la app y la app nunca lo mandó, no hay
    # `TX_OK` que contar ni fila que buscar: las dos columnas de la comparación
    # anterior darían cero y todo parecería en orden. Lo único que delata ese
    # caso es que haya una recepción sin su entrega correspondiente.
    #
    # UNA TRAMPA AL CONTAR RECEPCIONES
    # ---------------------------------
    # Hasta el 2026-09-05, la app y la fachada escribían las dos con fase `RX`,
    # así que contar entradas `RX` daba el DOBLE de eventos recibidos. Desde
    # entonces la app usa `RX_APP` y quedan separadas.
    #
    # Para los registros anteriores a esa fecha el discriminador es la presencia
    # del campo `entry.ts`: solo las entradas que escribe la librería lo llevan.
    # Por eso la consulta separa por ese campo y no solo por la fase.

    _sql = f"""
        SELECT JSON_VALUE(l.value,'$.entry.fase') AS fase,
               JSON_VALUE(l.value,'$.entry.tipo') AS tipo,
               CASE WHEN JSON_VALUE(l.value,'$.entry.ts') IS NULL
                    THEN 'la escribe la app' ELSE 'la escribe la libreria' END AS emisor,
               COUNT(*) AS cantidad
        FROM SentianceEventos e
        CROSS APPLY OPENJSON(e.json,'$.lineas') l
        WHERE e.tipo = 'AuditLogBatch'
          AND e.sentianceid = '{sid}'
          AND JSON_VALUE(l.value,'$.entry.fase') IN ('RX','RX_APP','TX_IN','TX_OK')
        GROUP BY JSON_VALUE(l.value,'$.entry.fase'),
                 JSON_VALUE(l.value,'$.entry.tipo'),
                 CASE WHEN JSON_VALUE(l.value,'$.entry.ts') IS NULL
                      THEN 'la escribe la app' ELSE 'la escribe la libreria' END
        ORDER BY tipo, fase
    """

    fases = pd.read_sql(_sql, engine)

    mo.vstack(
        [
            mo.md("### Recepción contra entrega, dentro del registro"),
            mo.md(
                "Las entradas con fase `RX` que **escribe la librería** son las "
                "recepciones reales. Las que escribe la app son una anotación "
                "propia sobre el mismo evento, y no cuentan como uno más."
            ),
            mo.ui.table(fases, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(engine, mo, pd, sid):
    # =========================================================================
    # FALLOS DECLARADOS Y LÍNEAS ILEGIBLES
    # =========================================================================
    # Las dos comparaciones anteriores cuentan cantidades. Esta busca las fases
    # que declaran un problema de forma explícita:
    #
    #   TX_FAIL      el envío falló y el evento quedó en la cola
    #   TX_DROP      el evento se descartó sin entregarse
    #   FLUSH_ERROR  el vaciado de la cola lanzó un error
    #   FLUSH_SKIP   el vaciado se canceló en una compuerta
    #   ERROR        la app registró un error propio
    #   SIN_CRUDO    un evento perdió su dato original del SDK
    #
    # Aparte están las líneas ilegibles. Cuando la app arma el lote, convierte
    # cada línea del archivo de texto a un objeto; las que no puede convertir las
    # cuenta en `lineasIlegibles` en vez de descartar el archivo entero. Un corte
    # a mitad de escritura daña la última línea y el resto sigue sirviendo.
    #
    # Si acá aparece algo, la comparación de cantidades de arriba no alcanza para
    # explicar lo que pasó.

    _sql = f"""
        SELECT JSON_VALUE(l.value,'$.entry.fase') AS fase,
               JSON_VALUE(l.value,'$.entry.tipo') AS tipo,
               JSON_VALUE(l.value,'$.entry.err') AS error,
               COUNT(*) AS cantidad
        FROM SentianceEventos e
        CROSS APPLY OPENJSON(e.json,'$.lineas') l
        WHERE e.tipo = 'AuditLogBatch'
          AND e.sentianceid = '{sid}'
          AND JSON_VALUE(l.value,'$.entry.fase') IN
              ('TX_FAIL','TX_DROP','FLUSH_ERROR','FLUSH_SKIP','ERROR','SIN_CRUDO')
        GROUP BY JSON_VALUE(l.value,'$.entry.fase'),
                 JSON_VALUE(l.value,'$.entry.tipo'),
                 JSON_VALUE(l.value,'$.entry.err')
        ORDER BY cantidad DESC
    """

    _sql_ilegibles = f"""
        SELECT JSON_VALUE(json,'$.archivo') AS archivo,
               JSON_VALUE(json,'$.lineasIlegibles') AS ilegibles,
               fechahora
        FROM SentianceEventos
        WHERE tipo = 'AuditLogBatch'
          AND sentianceid = '{sid}'
          AND JSON_VALUE(json,'$.lineasIlegibles') <> '0'
        ORDER BY fechahora DESC
    """

    fallos = pd.read_sql(_sql, engine)
    ilegibles = pd.read_sql(_sql_ilegibles, engine)

    _hay = len(fallos) > 0 or len(ilegibles) > 0
    mo.vstack(
        [
            mo.md("### Fallos"),
            mo.md("Sin fallos ni líneas ilegibles.").callout(kind="success")
            if not _hay
            else mo.vstack(
                [
                    mo.md(
                        f"**{len(fallos)} clases de fallo, {len(ilegibles)} lotes con líneas ilegibles.**"
                    ).callout(kind="danger"),
                    mo.ui.table(fallos, selection=None) if len(fallos) else mo.md(""),
                    mo.ui.table(ilegibles, selection=None) if len(ilegibles) else mo.md(""),
                ]
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()

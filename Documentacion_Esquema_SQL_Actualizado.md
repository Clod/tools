# Documentación del Esquema de Base de Datos (Sentiance)

## Objetivo
El objetivo de esta base de datos es procesar, estructurar y almacenar de manera persistente y consultable toda la telemetría y eventos de conducción obtenidos a través del SDK de Sentiance. Este esquema permite el análisis posterior de patrones de manejo, la calificación de usuarios (scoring), y la integración con modelos de negocio de aseguradoras (ej. IKE) para evaluación de riesgos, basándose en trayectos verificados, roles de los ocupantes e incidentes geolocalizados.

> [!NOTE]
> **Diferencias Clave con el Diseño Original de IKE:**
> 1. Todas las tablas finales incluyen campos internos de auditoría/ingesta que no existían en el diseño original: `IdOffload` y `FechaOffload`.
> 2. Se han descartado de esta documentación las tablas intermedias ("staging tables" como `MovDebug_Eventos` y `SentianceEventos`) ya que son exclusivas del pipeline temporal de procesamiento y no almacenan datos definitivos para consumo.
> 3. Tipos de datos estandarizados al formato SQL Server (`nvarchar`, `float`, `datetime`, `text`).

---

## Diccionario de Datos

A continuación se detalla la estructura **real y definitiva** de las tablas implementadas en Microsoft SQL Server, incluyendo la descripción de cada columna.

### 1. Tabla: `Transporte`
Almacena la información general e indicadores macroscópicos de un viaje cerrado.

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `IdOffload` | `int` | Sí | Log de ingesta del bucket/lote. | **[NUEVO]** |
| `FechaOffload` | `date` | Sí | Fecha de procesamiento local en la BD. | **[NUEVO]** |
| `usuario` | `nvarchar` | No | Identificador del usuario. | Equivalente (`userId`). |
| `viaje` | `nvarchar` | No | Identificador único del viaje (UUID). | Equivalente (`tripId`). |
| `modo_transporte` | `nvarchar` | No | Medio de transporte inferido (ej. `CAR`). | Equivalente. |
| `comienzo` | `datetime` | No | Fecha y hora de inicio del viaje. | Equivalente (Timestamp). |
| `fin` | `datetime` | No | Fecha y hora de fin del viaje. | Equivalente (Timestamp). |
| `duracion` | `int` | No | Duración total del viaje en segundos. | Equivalente. |
| `metadata` | `text` | Sí | Metadatos adicionales; contenedor para payloads JSON. | **[NUEVO]** |
| `velocidad_maxima` | `float` | No | Velocidad máxima alcanzada durante el viaje. | Equivalente. |

---

### 2. Tabla: `Recorridos`
Maneja la información geoespacial de la ruta trazada por el dispositivo móvil.

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `IdOffload` | `int` | Sí | Log de ingesta del bucket/lote. | **[NUEVO]** |
| `FechaOffload` | `date` | Sí | Fecha de procesamiento local. | **[NUEVO]** |
| `usuario` | `nvarchar` | No | Identificador del usuario. | Equivalente. |
| `viaje` | `nvarchar` | No | Identificador único del viaje. | Equivalente. |
| `distancia_m` | `float` | No | Distancia total recorrida en metros. | Equivalente. |
| `polyline` | `text` | No | Recorrido codificado geomorfológicamente. | Equivalente. **Nota:** Requiere compresión desde array de waypoints. |
| `puntos_recorrido` | `text` | Sí | Lista JSON de puntos crudos con latitud/longitud. | Equivalente. |
| `ubicacion_inicio` | `text` | Sí | Ubicación inicial estimada (Lat/Lon). | Equivalente. |
| `ubicacion_fin` | `text` | Sí | Ubicación final estimada (Lat/Lon). | Equivalente. |
| `maxima_velocidad` | `float` | No | Máxima velocidad registrada en un waypoint. | Equivalente. Redundante con `Transporte`. |

---

### 3. Tabla: `Conduccion`
Define los atributos de rol (piloto vs pasajero) identificados mediante la IA de clasificación en la nube de Sentiance.

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `id` | `int` | No | Llave primaria autonumérica de la tabla. | **[NUEVO]** (Identity). |
| `registro` | `datetime` | Sí | Momento de cálculo e inserción en base. | **[REEMPLAZA]** A "actualizacion". |
| `usuario` | `nvarchar` | No | Identificador de usuario. | Equivalente. |
| `viaje` | `nvarchar` | No | Identificador de viaje. | Equivalente. |
| `ocupante` | `varchar` | Sí | Rol inferido (ej. `DRIVER`, `PASSENGER`). | Equivalente. |

---

### 4. Tabla: `Eventos`
> [!TIP]
> **Diseño Evolutivo:** Actualmente la tabla `Eventos` contiene la captura completa de la telemetría bruta de incidentes reportados por Sentiance (aceleraciones, frenados, uso del celular, etc).

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `IdOffload` | `int` | Sí | Log de ingesta del bucket/lote. | **[NUEVO]** |
| `FechaOffload` | `date` | Sí | Fecha de procesamiento local. | **[NUEVO]** |
| `usuario` | `nvarchar` | No | Identificador de usuario. | Equivalente. |
| `viaje` | `nvarchar` | No | Identificador de viaje. | Equivalente. |
| `aceleracion` | `text` | No | Lista JSON de aceleraciones. | Consolida múltiples filas en un simple array/objeto. |
| `uso_telefono` | `text` | No | Eventos registrados sobre uso general de teléfono móvil. | **[NUEVO]** |
| `curvas` | `text` | No | Detalles de curvas bruscas tomadas. | Equivalente adaptado a `text`. |
| `celular_fijo` | `text` | No | Interacciones con el teléfono cuando estaba fijo en soporte. | Equivalente adaptado a `text`. |
| `frenado` | `text` | No | Lista JSON de frenadas. | Equivalente adaptado a `text`. |
| `exceso_velocidad`| `text` | No | Registros desglosados de excesos de velocidad. | **[REEMPLAZA]** Se corrigió la sintaxis de "exceso_de_velocid ad". |
| `llamados` | `text` | No | Eventos JSON de llamadas de voz detectadas. | Equivalente adaptado a `text`. |
| `pantalla` | `text` | No | Detalles sobre toques o iteracción con la pantalla del celular. | Equivalente adaptado a `text`. |

---

### 5. Tabla: `EventosSignificantes`
> [!TIP]
> **Diseño Evolutivo:** Esta tabla posee la misma estructura que `Eventos`. Se ha creado metodológicamente de manera separada en preparación para incorporar  **umbrales de severidad** de negocio. Así, un incidente puede existir en `Eventos`, pero sólo se insertará en `EventosSignificantes` si supera la exigencia de gravedad IKE (ej. exceso sostenido muy grave).

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `IdOffload` | `int` | Sí | Log de ingesta del bucket/lote. | **[NUEVO]** |
| `FechaOffload` | `date` | Sí | Fecha de procesamiento local. | **[NUEVO]** |
| `usuario` | `nvarchar` | No | Identificador de usuario. | Equivalente. |
| `viaje` | `nvarchar` | No | Identificador de viaje. | Equivalente. |
| `aceleracion` | `text` | No | Lista JSON de aceleraciones verdaderamente fuertes. | Consolida múltiples eventos. |
| `uso_telefono` | `text` | No | Eventos registrados sobre uso severo del teléfono móvil. | **[NUEVO]** |
| `curvas` | `text` | No | Detalles de curvas extremadamente bruscas tomadas gravadas. | Equivalente. |
| `celular_fijo` | `text` | No | Interacciones severas y prolongadas en soporte. | Equivalente. |
| `frenado` | `text` | No | Lista JSON de frenadas críticas de asfalto. | Equivalente. |
| `exceso_velocidad`| `text` | No | Registros desglosados de excesos de alta velocidad continuos. | **[REEMPLAZA]** |
| `llamados` | `text` | No | Llamadas distraídas con factor multiriesgo. | Equivalente. |
| `pantalla` | `text` | No | Iteracción grave in-transit. | Equivalente. |

---

### 6. Tabla: `PuntajesPrirmariosTr`
Almacena los top-scores o calificaciones principales del viaje evaluados algorítmicamente. Se construyen generalmente desde el objeto interno `safetyScores`.

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `IdOffload` | `int` | Sí | Log de ingesta del bucket/lote. | **[NUEVO]** |
| `FechaOffload` | `date` | Sí | Fecha de procesamiento local. | **[NUEVO]** |
| `usuario` | `nvarchar` | No | Identificador de usuario. | Equivalente. |
| `viaje` | `nvarchar` | No | Identificador de viaje. | Equivalente. |
| `legal` | `float` | No | Puntuación de legalidad ("legalScore"). | Equivalente. |
| `suavidad` | `float` | No | Puntuación global de suavidad ("smoothScore"). | Equivalente. |
| `atencion` | `float` | No | Puntuación global de atención ("focusScore"). | Equivalente. |
| `promedio` | `float` | No | Media o puntuación final consolidada ("overallScore"). | Equivalente. |

---

### 7. Tabla: `PuntajesSecundariosTr`
Almacena las sub-métricas o deméritos algorítmicos específicos del viaje. Estos explican por qué bajaron los "Puntajes Primarios".

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `IdOffload` | `int` | Sí | Log de ingesta del bucket/lote. | **[NUEVO]** |
| `FechaOffload` | `date` | Sí | Fecha de procesamiento local. | **[NUEVO]** |
| `usuario` | `nvarchar` | No | Identificador de usuario. | Equivalente. |
| `viaje` | `nvarchar` | No | Identificador de viaje. | Equivalente. |
| `concentracion` | `float` | No | Puntuación de concentración, relacionada a llamadas. | Equivalente (`callWhileMovingScore`). |
| `aceleracion_fuerte`| `float` | No | Penalidad numérica por aceleraciones violentas. | Equivalente. |
| `frenado_fuerte`| `float` | No | Penalidad numérica por frenados bruscos excesivos. | Equivalente. |
| `curvas_fuertes`| `float` | No | Penalidad numérica debido a giros fuertes. | Equivalente. |
| `anticipacion` | `float` | No | Sub-puntuación de la anticipación del chofer al frenar/acelerar. | Equivalente. |
| `celular_fijo` | `int` | No | Penalización global por el uso de celular fijo validada en número. | Equivalente. Modificado a `int` localmente. |
| `eventos_fuertes`| `int` | No | Penalización agregada / cuenta global referida a eventos violentos. | Equivalente. Modificado a `int` localmente. |

### 8. Tabla: `ChoqueDeVehiculo`
Almacena eventos específicos de colisión vehicular detectados por el sistema de IA integral.

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `Id` | `int` | No | Llave primaria autonumérica. | **[NUEVO]** |
| `Registro` | `datetime` | Sí | Fecha de recepción en base de datos. | **[NUEVO]** |
| `EventoId` | `int` | Sí | Referencia al ID del evento. | **[NUEVO]** |
| `usuario` | `varchar` | Sí | Identificador del usuario. | Equivalente. |
| `LeidoFechaHora` | `datetime` | Sí | Marca de tiempo de lectura. | **[NUEVO]** |
| `json` | `varchar` | Sí | Payload en bruto con los detalles de telemetría pre-choque y post-choque. | **[NUEVO]** |

---

### 9. Tabla: `PerfilDeUsuario`
Almacena y mantiene el perfil, historial semántico y predicciones asociadas a patrones de rutina del usuario.

| Columna SQL | Tipo de Dato | Opcional | Descripción | Original en IKE (Diferencias) |
|---|---|---|---|---|
| `Id` | `int` | No | Llave primaria autonumérica. | **[NUEVO]** |
| `Registro` | `datetime` | Sí | Fecha de recepción/actualización del perfil. | **[NUEVO]** |
| `EventoId` | `int` | Sí | Referencia al evento o batch asociado. | **[NUEVO]** |
| `usuario` | `varchar` | Sí | Identificador único del usuario global. | Equivalente. |
| `LeidoFechaHora` | `datetime` | Sí | Marca de tiempo de lectura u orquestación. | **[NUEVO]** |
| `json` | `varchar` | Sí | Payload con el perfil extendido arrojado por el SDK. | **[NUEVO]** |

---
**Generado Automáticamente:** Las estructuras reflejadas arriba incluyen las descripciones semánticas originales provistas y han sido cotejadas contra los nombres de columna y tipos de datos estrictos en Microsoft SQL Server.

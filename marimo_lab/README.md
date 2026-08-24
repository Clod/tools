# Laboratorio de Análisis Sentiance (Marimo Lab)

Este directorio contiene herramientas avanzadas para la exploración y el análisis de datos del SDK de Sentiance, utilizando notebooks interactivos de **Marimo** y procesamiento de lenguaje natural (IA).

## Contenido del DirectorIO

### 1. Explorador de Datos (`sentiance_data_explorer.py`)
Un notebook interactivo que permite navegar por los eventos almacenados en SQL Server.
*   **Funcionalidades**:
    *   Conexión a base de datos SQL Server.
    *   Filtros por `Sentiance ID` y rango de fechas.
    *   Visualización de JSON detallado.
    *   Extracción automática de datos geográficos (Venues/Paths) y visualización en mapa interactivo usando `leafmap`.

### 2. Analizador de JSON con IA (`sentiance_analyzer_ia.py`)
Notebook diseñado para pegar un objeto JSON de estado o evento y recibir un análisis detallado basado en la documentación oficial.
*   **Funcionalidades**:
    *   **Motor Gemini 2.5 Flash**: usa `google/gemini-2.5-flash` (contexto de 1M). El modelo se cambia en la constante `MODEL` de la celda `call_llm`.
    *   **Sistema de Logging Avanzado**: Incluye un "Debug Toggle" en la UI para ver trazas detalladas en tiempo real y diagnósticos de API.
    *   **Optimización de Tokens**: Limpieza inteligente de ruido en Markdown y selección dinámica de los top-10 conceptos globales.
    *   Extracción de palabras clave y búsqueda en índice `SALIDA.json`.
    *   Soporte para perfiles de visualización (Programador vs. Arquitecto).

### 3. Clasificador de Conceptos (`classify_concepts.py`)
Script que utiliza IA para identificar cuáles de los archivos de documentación son explicaciones conceptuales de alto nivel.
*   **Modelo**: `google/gemini-2.0-flash-001`, que **fue retirado de OpenRouter**. Este script fallará con un 404 hasta que se actualice.
*   **Prompt Refinado**: Clasifica estrictamente teoría core vs. guías de implementación.
*   **Propósito**: Crear una base de conocimientos "global" que se incluya en todos los análisis para dar contexto sobre el funcionamiento general del SDK.
*   **Genera**: `concepts.json`.

### 4. Constructor de Índice (`build_index.py`)
Script de utilidad para procesar la documentación scrapeada y generar un índice técnico.
*   **Funcionalidades**:
    *   Lee los archivos markdown de la documentación.
    *   Utiliza IA para extraer las 10 palabras claves más importantes de cada archivo.
    *   **Importante**: Incluye la URL de origen como el primer elemento de la lista de palabras clave.
    *   Genera el archivo `SALIDA.json`.

### 5. Archivos de Soporte
*   `SALIDA.json`: Índice de palabras clave generado.
*   `.env`: Credenciales (base de datos y OpenRouter). No versionado — copiar de `.env.example`.
*   `.env.example`: Plantilla de credenciales, sin valores.
*   `pyproject.toml`: Gestión de dependencias con `uv`.

## Para empezar (Explorador de Datos)

Si solo querés usar el explorador contra la base, son tres pasos.

**1. Requisitos.** Necesitás [`uv`](https://docs.astral.sh/uv/) instalado. No hace
falta crear ningún entorno ni instalar dependencias a mano: `uv` las resuelve a
partir del bloque `/// script` del propio notebook.

**2. Credenciales.** Copiá la plantilla y completá los valores:

```bash
cp .env.example .env
```

El explorador necesita `DB_SERVER`, `DB_NAME`, `DB_USER` y `DB_PASS`. `DB_PORT`
es opcional y asume `9433` si no está. Si el servidor está detrás de VPN,
conectate antes de abrir el notebook.

`.env` está en `.gitignore` y no debe commitearse nunca.

**3. Ejecutar.**

```bash
uv run marimo run sentiance_data_explorer.py     # interfaz limpia
uv run marimo edit sentiance_data_explorer.py    # con el código a la vista
```

Si falta alguna credencial, el propio notebook te lo dice al abrirlo en lugar de
fallar con un error de conexión.

> **Nota:** el explorador **no** se puede publicar como GitHub Page. Un navegador
> no puede abrir una conexión TCP contra SQL Server, y `pymssql` y `leafmap` no
> existen en el entorno WebAssembly que usa `marimo export html-wasm`. Verificado
> exportándolo y ejecutándolo: el notebook muere en el primer `import`.

---

## Instrucciones de Ejecución (resto de las herramientas)

Se recomienda el uso de `uv` para una gestión sencilla de dependencias.

### Preparación
Las herramientas de IA necesitan además `OPENROUTER_API_KEY` en el `.env`, y los
archivos de datos `SALIDA.json` y la documentación scrapeada, que **no están
versionados**. Si no los tenés, hay que generarlos con los pasos siguientes.

### Paso 1: Clasificar conceptos globales (Opcional si ya existe concepts.json)
```bash
uv run python classify_concepts.py /ruta/a/scraped_site concepts.json
```

### Paso 2: Construir el índice de documentación
Si has actualizado los archivos scrapeados, debes regenerar el índice:
```bash
uv run python build_index.py /ruta/a/scraped_site SALIDA.json
```

### Paso 3: Ejecutar el Analizador de IA
```bash
uv run marimo run sentiance_analyzer_ia.py
```

## Dependencias Principales
*   `marimo`: El motor de notebooks reactivos.
*   `leafmap`: Para la visualización de mapas.
*   `pandas`: Procesamiento de datos.
*   `sqlalchemy` & `pymssql`: Conexión a base de datos.
*   `requests`: Llamadas a la API de OpenRouter.

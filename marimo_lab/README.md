# Laboratorio de Análisis Sentiance (Marimo Lab)

Este directorio contiene herramientas avanzadas para la exploración y el análisis de datos del SDK de Sentiance, utilizando notebooks interactivos de **Marimo** y procesamiento de lenguaje natural (IA).

## Contenido del DirectorIO

### 1. Explorador de Datos (`app.py`)
Un notebook interactivo que permite navegar por los eventos almacenados en SQL Server.
*   **Funcionalidades**:
    *   Conexión a base de datos SQL Server.
    *   Filtros por `Sentiance ID` y rango de fechas.
    *   Visualización de JSON detallado.
    *   Extracción automática de datos geográficos (Venues/Paths) y visualización en mapa interactivo usando `leafmap`.

### 2. Analizador de JSON con IA (`sentiance_analyzer.py`)
Notebook diseñado para pegar un objeto JSON de estado o evento y recibir un análisis detallado basado en la documentación oficial.
*   **Funcionalidades**:
    *   Extracción de palabras clave del JSON.
    *   Búsqueda inteligente en el índice de documentación (`SALIDA.json`).
    *   Análisis contextual mediante modelos de IA (vía OpenRouter).
    *   Soporte para perfiles de visualización (Programador vs. Usuario Final).

### 3. Constructor de Índice (`build_index.py`)
Script de utilidad para procesar la documentación scrapeada y generar un índice técnico.
*   **Funcionalidades**:
    *   Lee los archivos markdown de la documentación.
    *   Utiliza IA para extraer las 10 palabras claves más importantes de cada archivo.
    *   **Importante**: Incluye la URL de origen como el primer elemento de la lista de palabras clave.
    *   Genera el archivo `SALIDA.json`.

### 4. Archivos de Soporte
*   `SALIDA.json`: Índice de palabras clave generado.
*   `.env`: Configuración de credenciales (OpenRouter API Key y credenciales de DB).
*   `pyproject.toml`: Gestión de dependencias con `uv`.

## Instrucciones de Ejecución

Se recomienda el uso de `uv` para una gestión sencilla de dependencias.

### Preparación
1.  Asegúrate de tener configurado el archivo `.env` con:
    ```env
    OPENROUTER_API_KEY=tu_clave_aqui
    DB_SERVER=servidor_sql
    DB_NAME=nombre_db
    DB_USER=usuario
    DB_PASS=contraseña
    ```

### Paso 1: Construir el índice de documentación
Si has actualizado los archivos scrapeados, debes regenerar el índice:
```bash
uv run python build_index.py /ruta/a/scraped_site SALIDA.json
```

### Paso 2: Ejecutar el Explorador de Datos
Para abrir el explorador en modo aplicación (interfaz limpia):
```bash
uv run marimo run app.py
```
Para abrirlo en modo edición (para modificar el código):
```bash
uv run marimo edit app.py
```

### Paso 3: Ejecutar el Analizador de IA
```bash
uv run marimo run sentiance_analyzer.py
```

## Dependencias Principales
*   `marimo`: El motor de notebooks reactivos.
*   `leafmap`: Para la visualización de mapas.
*   `pandas`: Procesamiento de datos.
*   `sqlalchemy` & `pymssql`: Conexión a base de datos.
*   `requests`: Llamadas a la API de OpenRouter.

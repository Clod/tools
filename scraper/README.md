# Documentador de Sentiance SDK

Este directorio contiene herramientas para extraer (scraping), combinar y limpiar la documentación oficial de Sentiance SDK, preparándola para su procesamiento por modelos de lenguaje (LLM).

## Estructura del Proyecto

*   `scraped_site/`: Directorio donde se guardan los archivos markdown individuales.
*   `crawler_sitemap.py`: El script de extracción principal basado en el sitemap.
*   `combine_markdown.py`: Script para fusionar todos los archivos markdown en uno solo.
*   `clean_documentation.py`: Script para limpiar el ruido (cabeceras, menús) del archivo combinado.
*   `pyproject.toml`: Configuración de dependencias para `uv`.

## Configuración del Entorno

Este proyecto utiliza `uv` para la gestión de dependencias y entornos virtuales.

1.  **Instalar dependencias:**
    ```bash
    uv pip install -r pyproject.toml
    ```
    *O simplemente ejecute los scripts con `uv run` como se muestra a continuación.*

2.  **Instalar navegadores de Playwright:**
    ```bash
    uv run playwright install chromium
    ```

## Scripts y Uso

Los scripts están diseñados para ejecutarse en orden:

### 1. Crawler (Sitemap) - `crawler_sitemap.py`
Este es el extractor más eficiente. Utiliza `crawl4ai` y el sitemap de GitBook para descargar solo lo necesario.
*   **Qué hace:** 
    *   Lee `sitemap.xml` para encontrar todas las páginas.
    *   **Extracción Condicional:** Compara la fecha de última modificación del servidor con el archivo local. Si no ha cambiado, omite la descarga.
    *   **Metadatos:** Agrega un encabezado `Source: URL` al inicio de cada archivo.
*   **Ejecución:**
    ```bash
    uv run python crawler_sitemap.py
    ```

### 2. Combinador - `combine_markdown.py`
Une todos los archivos individuales en un único documento maestro.
*   **Qué hace:** Lee `scraped_site/`, ordena los archivos alfabéticamente y los concatena en `combined_documentation.md`.
*   **Ejecución:**
    ```bash
    uv run python combine_markdown.py
    ```

### 3. Limpiador - `clean_documentation.py`
Procesa el archivo combinado para eliminar elementos repetitivos de la web.
*   **Qué hace:** 
    *   Elimina logotipos, menús de navegación lateral y pies de página de GitBook.
    *   Limpia atajos de teclado (como `Ctrl+k`) y botones de "Copy".
    *   Genera un archivo optimizado llamado `cleaned_documentation.md`.
*   **Ejecución:**
    ```bash
    uv run python clean_documentation.py
    ```

### 4. Crawler (Recursivo) - `crawler_tree.py` *(Opcional)*
Un extractor alternativo que navega de forma recursiva a través de los enlaces de la página de inicio.
*   **Uso:** Menos preciso que el de sitemap, pero útil si el sitemap no está disponible.
*   **Ejecución:**
    ```bash
    uv run python crawler_tree.py
    ```

## Flujo de Trabajo Recomendado

Para obtener una documentación limpia y actualizada:

1.  Ejecute `crawler_sitemap.py` para sincronizar los archivos locales.
2.  Ejecute `combine_markdown.py` para generar el archivo único.
3.  Ejecute `clean_documentation.py` para obtener la versión final lista para IA.

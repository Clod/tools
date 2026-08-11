"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                ANALIZADOR DE JSON DEL SDK SENTIANCE - MARIMO                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ QUÉ HACE ESTE NOTEBOOK:                                                      ║
║ - Recibe un JSON del SDK de Sentiance y explica qué significa, apoyándose    ║
║   en la documentación oficial scrapeada y en un LLM.                         ║
║ - Pipeline de 4 pasos:                                                       ║
║     1. Extrae recursivamente las keys y valores del JSON.                    ║
║     2. Un LLM elige hasta 4 archivos de doc relevantes usando el índice      ║
║        de keywords (SALIDA.json).                                            ║
║     3. Lee esos markdown y les quita el ruido de navegación de GitBook       ║
║        (logos, menús, links) para ahorrar tokens.                            ║
║     4. Un LLM produce el análisis final citando las URLs de origen.          ║
║ - Dos perspectivas seleccionables:                                           ║
║     · programmer → tipo, por qué se generó, significado de cada campo,       ║
║       calidad del dato y cómo usarlo.                                        ║
║     · architect  → tipo, por qué se generó y desglose de sub-registros.      ║
║ - La respuesta se genera en ESPAÑOL y siempre abre listando los links de     ║
║   la documentación utilizada.                                                ║
║ - El análisis NO corre solo: hay que apretar el botón 'Analyze JSON'.        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ENTRADAS REQUERIDAS:                                                         ║
║ - marimo_lab/.env con OPENROUTER_API_KEY                                     ║
║     Obligatorio. Sin esa variable el notebook aborta al iniciar.             ║
║ - marimo_lab/SALIDA.json                                                     ║
║     Índice de keywords por archivo. Lo genera build_index.py.                ║
║ - marimo_lab/concepts.json                                                   ║
║     Lista de docs conceptuales; se cargan los primeros 10 como contexto      ║
║     global. Lo genera classify_concepts.py. Si falta, se sigue sin él.       ║
║ - scraper/scraped_site/                                                      ║
║     Documentación de Sentiance scrapeada en markdown.                        ║
║                                                                              ║
║ OJO: BASE_DIR y DOCS_DIR están hardcodeados como rutas absolutas en la       ║
║ primera celda. Si movés el repo de lugar, hay que editarlas.                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ MODELO:                                                                      ║
║ - google/gemini-2.0-flash-001 vía OpenRouter, para el ruteo y el análisis.   ║
║ - Se puede cambiar en la constante MODEL de la celda call_llm.               ║
║ - temperature=0 para que las respuestas sean reproducibles.                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ CÓMO EJECUTAR ESTE NOTEBOOK:                                                 ║
║                                                                              ║
║ 1. CON UV (Recomendado):                                                     ║
║    $ uv run marimo edit sentiance_analyzer_ia.py                             ║
║    Instala automáticamente las dependencias del bloque /// script.           ║
║                                                                              ║
║ 2. MODO EDICIÓN (Tradicional):                                               ║
║    $ marimo edit sentiance_analyzer_ia.py                                    ║
║    Abre el IDE completo en el navegador para editar y ver salidas.           ║
║                                                                              ║
║ 3. MODO EJECUCIÓN (Interfaz limpia):                                         ║
║    $ marimo run sentiance_analyzer_ia.py                                     ║
║    Abre la app final - solo widgets y salidas, sin código.                   ║
║                                                                              ║
║ 4. EXPORTAR A HTML (Snapshot estático):                                      ║
║    $ marimo export html sentiance_analyzer_ia.py -o app.html                 ║
║    Crea un HTML estático, sin interactividad.                                ║
║                                                                              ║
║ 5. CONVERTIR A JUPYTER (Migración):                                          ║
║    $ marimo export ipynb sentiance_analyzer_ia.py -o app.ipynb               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import marimo

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "requests",
#     "python-dotenv",
# ]
# ///

__generated_with = "0.9.14"
app = marimo.App()


@app.cell
def __():
    """Setup and imports."""
    import marimo as mo
    import json
    import os
    import logging
    from pathlib import Path
    import requests
    import re
    from typing import Dict, List, Any
    from dotenv import load_dotenv
    
    # Load .env file
    load_dotenv()
    
    # OpenRouter config
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("sentiance_analyzer")
    
    # Validate API key
    if not OPENROUTER_API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY not found in .env file")
    
    # Paths - Use absolute paths for sandbox safety
    BASE_DIR = "/Users/claudiograsso/Documents/Sentiance/tools/marimo_lab"
    DOCS_DIR = "/Users/claudiograsso/Documents/Sentiance/tools/scraper/scraped_site"
    KEYWORDS_INDEX = os.path.join(BASE_DIR, "SALIDA.json")
    CONCEPTS_FILE = os.path.join(BASE_DIR, "concepts.json")
    
    mo.md("# 🔍 Sentiance SDK JSON Analyzer")
    return (
        BASE_DIR,
        CONCEPTS_FILE,
        DOCS_DIR,
        KEYWORDS_INDEX,
        mo,
        json,
        os,
        Path,
        requests,
        re,
        logging,
        logger,
        OPENROUTER_API_KEY,
        OPENROUTER_BASE_URL,
    )


@app.cell
def __(mo):
    """Rendered intro: what this notebook does and how to run it."""

    mo.md("""
    Analiza un **JSON del SDK de Sentiance** y explica qué significa, apoyándose
    en la documentación oficial y en un LLM.

    **Cómo funciona:** extrae las keys del JSON → un LLM elige hasta 4 archivos
    de documentación relevantes → los limpia de ruido de navegación → un LLM
    produce el análisis final, en español y citando las URLs que usó.

    **Cómo se usa:**

    1. Pegá el JSON en el cuadro de texto de abajo.
    2. Elegí la perspectiva: `programmer` (campos, calidad del dato, cómo usarlo)
       o `architect` (desglose de sub-registros).
    3. Apretá **🚀 Analyze JSON**. El análisis no corre solo.

    **Para correr el notebook:** `uv run marimo edit sentiance_analyzer_ia.py`
    (modo edición) o `marimo run sentiance_analyzer_ia.py` (interfaz limpia).
    Requiere `OPENROUTER_API_KEY` en `marimo_lab/.env`.

    Ver el docstring al principio del archivo para el detalle completo de
    entradas y modos de ejecución.
    """)
    return


@app.cell
def __(OPENROUTER_API_KEY, OPENROUTER_BASE_URL, logger, requests):
    """LLM API caller."""

    # Model selection - CHANGE THIS TO SAVE MONEY
    # MODEL = "google/gemini-2.0-flash-exp:free"  # FREE!
    MODEL = "qwen/qwen-2.5-72b-instruct"      # $0.35/1M (best paid)
    # MODEL = "mistralai/mistral-small"         # $0.20/1M (cheapest)
    # MODEL = "meta-llama/llama-3.1-8b-instruct:free"  # FREE
    MODEL = "google/gemini-2.0-flash-001"
    
    def call_llm(prompt: str, model: str = MODEL, max_tokens: int = 2048) -> str:
        """Call OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8080",
            "X-Title": "Sentiance Analyzer"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0
        }
        
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM API Error: {response.text}")
            raise e
        
        return response.json()["choices"][0]["message"]["content"]
    
    return call_llm,


@app.cell
def __(CONCEPTS_FILE, KEYWORDS_INDEX, json):
    """Load keyword index."""
    
    with open(KEYWORDS_INDEX, 'r') as f:
        keyword_index = json.load(f)
    
    # Load global concepts
    try:
        with open(CONCEPTS_FILE, 'r') as f:
            global_concepts = json.load(f)
    except FileNotFoundError:
        global_concepts = []
    
    print(f"✅ Loaded keyword index: {len(keyword_index)} files")
    print(f"🧠 Loaded global concepts: {len(global_concepts)} files")
    
    return global_concepts, keyword_index


@app.cell
def __(DOCS_DIR, Path, call_llm, global_concepts, json, keyword_index, logger, re):
    """Main analyzer class."""
    
    class SentianceAnalyzer:
        def __init__(self, keyword_index: dict, global_concepts: list, docs_dir: str):
            self.keyword_index = keyword_index
            self.global_concepts = global_concepts
            self.docs_dir = docs_dir
            self._file_cache = {}
            self._conceptual_content = ""
            
            # Pre-load conceptual content
            self._load_global_context()
        
        def clean_markdown_content(self, text: str) -> str:
            """
            Strips navigation noise, logos, and flattens links to save tokens.
            Preserves the 'Source: <URL>' line.
            """
            lines = text.split('\n')
            cleaned_lines = []
            
            # 1. Patterns to skip entirely
            skip_patterns = [
                r'^bars\[!\[Logo\]', # GitBook logo/nav header
                r'^search$',
                r'^circle-xmark$',
                r'^`Ctrl``k`$',
                r'^Moreellipsischevron-down$',
                r'^chevron-upchevron-down$',
                r'^\[gitbookPowered by GitBook\]',
                r'^xmark$',
                r'^block-quoteOn this page',
                r'^sun-brightdesktopmoon$',
                r'^copyCopychevron-down$',
                r'^\[hashtag\]',
                r'^circle-exclamation$',
                r'^circle-info$',
                r'^\[Previous.*\]\(.*\)', # Nav links
                r'^\[Next.*\]\(.*\)',
                r'^Last updated .* ago$',
            ]
            
            # 2. Sidebar/Menu link pattern: '* [Text](https://docs.sentiance.com/...)'
            menu_link_pattern = re.compile(r'^\s*\* \[.*\]\(https://docs\.sentiance\.com/.*\)$')
            
            for line in lines:
                line_trimmed = line.strip()
                
                # Keep Source URL
                if line_trimmed.startswith("Source:"):
                    cleaned_lines.append(line)
                    continue
                
                # Skip noise patterns
                if any(re.search(p, line_trimmed) for p in skip_patterns):
                    continue
                
                # Skip menu/sidebar links
                if menu_link_pattern.match(line_trimmed):
                    continue
                
                # 3. Flatten links: [Text](URL) -> Text (except for things that look like actual info)
                # But keep code blocks as is
                if '```' not in line:
                    line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
                
                # 4. Remove image markers
                line = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', line)
                
                if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)

        def _load_global_context(self):
            """Load a subset of conceptual files to avoid token bloat (max 10)."""
            contents = []
            # Sort concepts to be deterministic, pick top 10 (likely core summaries)
            for filename in sorted(self.global_concepts)[:10]:
                filepath = Path(self.docs_dir) / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # Clean and truncate
                        raw_text = f.read()[:2000]
                        cleaned_text = self.clean_markdown_content(raw_text)
                        contents.append(f"### CONCEPT: {filename}\n{cleaned_text}")
            self._conceptual_content = "\n\n".join(contents)
            logger.info(f"Global context loaded: {len(contents)} conceptual files (~{len(self._conceptual_content)} chars)")
        
        def analyze_json(self, json_obj: dict, view: str = "programmer") -> dict:
            """
            Full pipeline: JSON → keyword match → select docs → analyze
            """
            
            # Step 1: Extract keywords from JSON
            json_keywords = self._extract_json_keywords(json_obj)
            logger.debug(f"🔑 JSON keywords: {json_keywords}")
            
            # Step 2: LLM picks best files from keyword index
            selected_files = self._llm_select_files(json_obj, json_keywords)
            logger.info(f"📄 Selected files: {selected_files}")
            
            # Step 3: Read selected files
            docs_content = self._read_files(selected_files)
            logger.debug(f"📖 Read {len(docs_content)} files ({sum(len(v) for v in docs_content.values())} chars)")
            
            # Step 4: LLM final analysis
            analysis = self._llm_analyze(json_obj, docs_content, view)
            logger.info(f"Analysis complete (Length: {len(analysis)})")
            
            return {
                "json_keywords": json_keywords,
                "selected_files": selected_files,
                "analysis": analysis
            }
        
        def _extract_json_keywords(self, json_obj: dict) -> list:
            """Extract keywords from JSON fields."""
            keywords = []
            
            def extract_recursive(obj, prefix=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        keywords.append(key)
                        if isinstance(value, str):
                            keywords.append(value)
                        extract_recursive(value, key)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_recursive(item, prefix)
            
            extract_recursive(json_obj)
            return list(set(keywords))
        
        def _llm_select_files(self, json_obj: dict, json_keywords: list) -> list:
            """LLM picks best files using keyword index."""
            
            # Truncate keyword index if too large
            index_str = json.dumps(self.keyword_index, indent=2)
            if len(index_str) > 10000:
                index_str = index_str[:10000] + "\n... (truncated)"
            
            prompt = f"""
Analyze this Sentiance SDK JSON:
{json.dumps(json_obj, indent=2)}

JSON keywords extracted: {json_keywords}

Available documentation files with their keywords (the FIRST element of each list is the Source URL):
{index_str}

["filename1.md", "filename2.md", "filename3.md"]

No explanations, just the JSON array.
"""
            
            # Debug: Log the prompt
            logger.debug(f"Router Prompt (Length: {len(prompt)} chars). Head:\n{prompt[:500]}...")
            
            # Use Gemini 2.0 Flash (User Requested)
            response = call_llm(prompt, model="google/gemini-2.0-flash-001", max_tokens=1024)
            
            # Debug: Log raw response
            logger.debug(f"Router Raw Response:\n{response}")
            
            # Extract JSON array
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                try:
                    selected = json.loads(json_match.group())
                    return selected[:4]  # Max 4 files
                except json.JSONDecodeError as e:
                    logger.error(f"Router JSON Parse Error: {e}")
            else:
                logger.warning("Router Regex Failed to find JSON array")
            
            return []
        
        def _read_files(self, filenames: list) -> dict:
            """Read selected documentation files."""
            docs_content = {}
            
            for filename in filenames:
                filepath = Path(self.docs_dir) / filename
                
                if not filepath.exists():
                    logger.warning(f"File not found: {filename}")
                    continue
                
                if filename not in self._file_cache:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # Read and clean content
                        raw_text = f.read()[:4000]
                        self._file_cache[filename] = self.clean_markdown_content(raw_text)
                        logger.debug(f"Cached cleaner version of {filename}")
                
                docs_content[filename] = self._file_cache[filename]
            
            return docs_content
        
        def _llm_analyze(self, json_obj: dict, docs_content: dict, view: str) -> str:
            """LLM analyzes JSON using selected documentation."""
            
            common_instructions = """
INSTRUCCIONES IMPORTANTES:
1. Comienza tu respuesta con una sección titulada "### 🔗 Documentación Utilizada" listando los links (URLs) de origen de todos los archivos proporcionados. Estos links se encuentran al principio de cada archivo como "Source: <URL>".
2. Proporciona toda tu respuesta en ESPAÑOL.
"""

            if view == "programmer":
                perspective = f"""
{common_instructions}
Estás analizando para un PROGRAMADOR. Proporciona:
1. **Tipo**: ¿Qué objeto del SDK es este?
2. **Por qué se generó**: ¿Por qué el SDK crearía este registro?
3. **Significado de los campos**: ¿Qué significa cada campo (según la documentación)?
4. **Calidad de los datos**: ¿Es un registro válido? ¿Algún problema?
5. **Cómo usarlo**: ¿Qué debe hacer un programador con estos datos?
"""
            else:  # architect
                perspective = f"""
{common_instructions}
Estás analizando para un ARQUITECTO DE SOFTWARE. Proporciona:
1. **Tipo**: ¿Qué objeto del SDK es este?
2. **Por qué se generó**: ¿Por qué el SDK crearía este registro?
3. **Análisis de sub-registros**: Analiza los sub-registros de este registro. Da una explicación para cada uno e incluye el JSON correspondiente.
"""
            
            prompt = f"""
{perspective}

JSON a analizar:
{json.dumps(json_obj, indent=2)}

---
CONTEXTO CONCEPTUAL GLOBAL (Sentiance SDK Fundamentals):
{self._conceptual_content}

---
DOCUMENTACIÓN ESPECÍFICA (seleccionada para este JSON):
{self._format_docs(docs_content)}

Basado en la DOCUMENTACIÓN REAL anterior, proporciona un análisis detallado.
Usa un formato claro con encabezados y viñetas.
"""
            
            # Debug: Log analysis prompt
            logger.debug(f"Analysis Prompt (Length: {len(prompt)} chars). Head:\n{prompt[:500]}...")
            
            response = call_llm(prompt, max_tokens=2048)
            
            # Debug: Log analysis response
            if not response:
                logger.error("Analysis Response is EMPTY!")
            else:
                logger.debug(f"Analysis Raw Response (Length: {len(response)} chars)")
            
            return response
        
        def _format_docs(self, docs_content: dict) -> str:
            """Format docs for LLM prompt."""
            formatted = []
            for filename, content in docs_content.items():
                formatted.append(f"### File: {filename}\n{content}\n")
            return "\n".join(formatted)
    
    # Initialize analyzer
    analyzer = SentianceAnalyzer(keyword_index, global_concepts, DOCS_DIR)
    
    return SentianceAnalyzer, analyzer


@app.cell
def __(mo):
    """Input: JSON to analyze."""
    
    mo.md("""
    ## 📋 Input JSON
    Paste your Sentiance SDK JSON below:
    """)
    
    json_input = mo.ui.text_area(
        placeholder="""{
  "event_type": "TRANSPORT",
  "transport_mode": "CAR",
  "distance": 12.5,
  "duration": 3600,
  "start_location": {"lat": 40.7128, "lon": -74.0060}
}""",
        rows=10,
        full_width=True
    )
    
    return json_input,


@app.cell
def __(json_input):
    json_input
    return


@app.cell
def __(mo):
    """Debug toggle definition."""
    debug_toggle = mo.ui.checkbox(label="Enable Debug Logs (Verbose Console Output)", value=False)
    debug_toggle
    return debug_toggle,


@app.cell
def __(debug_toggle, logging, logger):
    """React to debug toggle."""
    # Apply toggle
    if debug_toggle.value:
        # Enable debug for OUR logger
        logger.setLevel(logging.DEBUG)
        
        # Suppress noise from libraries
        logging.getLogger("markdown").setLevel(logging.WARNING)
        logging.getLogger("pymdownx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        logger.debug("Debug logging ENABLED (External noise suppressed)")
    else:
        logger.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
    return


@app.cell
def __(mo):
    """View selector."""
    
    mo.md("## 👁️ Analysis View")
    
    view_selector = mo.ui.dropdown(
        options=["programmer", "architect"],
        value="programmer",
        label="Select perspective:"
    )
    
    return view_selector,


@app.cell
def __(view_selector):
    view_selector
    return


@app.cell
def __(mo):
    # Step 1: Use run_button - specifically designed to trigger expensive cells
    analyze_btn = mo.ui.run_button(
        label="🚀 Analyze JSON", 
        kind="success", 
        full_width=True
    )
    
    mo.md("### ⚙️ Step 2: Configure & Run")
    analyze_btn
    return (analyze_btn,)


@app.cell
def __(analyze_btn, analyzer, json, json_input, logger, mo, view_selector):
    import ast
    import traceback
    import time

    def parse_payload(text):
        """Parsea JSON, o la representacion de un dict de Python.

        Los datos del SDK suelen llegar como repr de un dict de Python
        (`True` / `False` / `None` y comillas simples) en vez de JSON, porque
        se copian desde una consola o desde el explorador de datos.
        `ast.literal_eval` solo evalua literales -numeros, cadenas, booleanos,
        listas y diccionarios-, de modo que no ejecuta codigo.

        Devuelve (objeto, fue_convertido). Si tampoco es un literal valido,
        propaga el error original de JSON, que indica linea y columna.

        Exige un objeto o una lista en la raiz: un escalar suelto como `42`
        es JSON valido, pero produciria un analisis vacio en vez de un error.
        """
        def require_container(obj, on_error):
            if not isinstance(obj, (dict, list)):
                raise on_error from None
            return obj

        not_a_container = json.JSONDecodeError(
            "Se esperaba un objeto o una lista en la raiz", text or "", 0
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as json_error:
            try:
                obj = ast.literal_eval(text)
            except (ValueError, SyntaxError, MemoryError, RecursionError):
                raise json_error from None
            return require_container(obj, json_error), True
        return require_container(parsed, not_a_container), False

    # This cell ONLY triggers when the run_button is clicked
    ts = time.strftime("%H:%M:%S")
    
    if analyze_btn.value:
        logger.info(f"⚡ Analysis starting (Triggered at {ts})")
        
        try:
            raw_input = json_input.value.strip()
            if not raw_input:
                 logger.warning("Empty JSON input provided")
                 rendered_output = mo.md("⚠️ **Please provide some JSON data**")
            else:
                json_obj, was_python_literal = parse_payload(raw_input)
                if was_python_literal:
                    logger.info(
                        "Input parsed as a Python literal (True/False/None) "
                        "and converted to JSON"
                    )
                    conversion_notice = (
                        "> ℹ️ La entrada era un diccionario de Python, no JSON. "
                        "Se convirtio automaticamente.\n\n"
                    )
                else:
                    logger.info("JSON input successfully parsed")
                    conversion_notice = ""

                with mo.status.spinner(title="Contacting AI...") as status_box:
                    result = analyzer.analyze_json(json_obj, view=view_selector.value)
                
                logger.info("LLM Pipeline complete")
                
                # Check for empty analysis body
                if not result.get('analysis'):
                    logger.error("LLM returned an empty analysis string!")
                    analysis_body = "⚠️ *The AI failed to generate an analysis. Check logs for details.*"
                else:
                    analysis_body = result['analysis']

                rendered_output = mo.md(f"""
### ✅ Analysis Complete (at {ts})

{conversion_notice}**Keywords:** {', '.join(result['json_keywords'][:8])}
**Docs Used:** {', '.join(result['selected_files']) if result['selected_files'] else 'None found'}

---

{analysis_body}
""")
                 
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")

            # Mostrar la linea exacta que fallo con un cursor en la columna.
            # El mensaje crudo de json solo da numeros, que obligan a contar
            # lineas a mano sobre un JSON largo.
            input_lines = raw_input.splitlines()
            if 1 <= e.lineno <= len(input_lines):
                bad_line = input_lines[e.lineno - 1]
                cursor = " " * max(e.colno - 1, 0) + "^"
                location = f"\n```\n{bad_line}\n{cursor}\n```\n"
            else:
                location = ""

            # "Expecting value" es casi siempre un dict de Python pegado como
            # si fuera JSON. Los otros mensajes ya son autoexplicativos.
            if e.msg == "Expecting value":
                hint = (
                    "\nEsto suele pasar cuando el texto es la representacion de un "
                    "**diccionario de Python**, no JSON. Revisa que no haya "
                    "`None`, `True` o `False`, que en JSON se escriben `null`, "
                    "`true` y `false`."
                )
            else:
                hint = ""

            rendered_output = mo.md(
                f"❌ **JSON invalido** — {e.msg}, linea {e.lineno}, columna {e.colno}"
                f"\n{location}{hint}"
            )
        except Exception as e:
            logger.error(f"Critical Exception: {e}\n{traceback.format_exc()}")
            rendered_output = mo.vstack([
                mo.md(f"❌ **Error**: {e}"),
                mo.accordion({"Technical Traceback": mo.md(f"```python\n{traceback.format_exc()}\n```")})
            ])
        finally:
            logger.info("🏁 Analysis cell completion")
    else:
        rendered_output = mo.md("_Paste JSON above and click 'Analyze JSON' to start_")

    # Final expression for Marimo to display
    rendered_output
    return (rendered_output,)


@app.cell
def __(mo):
    """Example JSONs."""
    
    mo.md("""
    ---
    
    ## 📚 Example JSONs
    
    ### Transport Event
    ```json
    {
      "event_type": "TRANSPORT",
      "transport_mode": "CAR",
      "distance": 12.5,
      "duration": 3600,
      "start_location": {"lat": 40.7128, "lon": -74.0060},
      "end_location": {"lat": 40.7589, "lon": -73.9851}
    }
    ```
    
    ### Crash Event
    ```json
    {
      "crash_severity": "SEVERE",
      "timestamp": 1621500000000,
      "location": {"lat": 40.7128, "lon": -74.0060},
      "user_activity": "DRIVING",
      "diagnostic": {
        "max_impact_magnitude": 45.2,
        "impact_direction": "FRONT",
        "time_to_impact": 0.15
      }
    }
    ```
    
    ### SDK Status
    ```json
    {
      "detection_status": "ENABLED_AND_DETECTING",
      "can_detect": true,
      "location_permission": "GRANTED",
      "location_setting": "HIGH_ACCURACY",
      "battery_optimization_setting": "UNRESTRICTED"
    }
    ```
    """)
    
    return


if __name__ == "__main__":
    app.run()

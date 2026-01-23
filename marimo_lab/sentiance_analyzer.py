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
    
    # Validate API key
    if not OPENROUTER_API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY not found in .env file")
    
    # Paths
    DOCS_DIR = "/Users/claudiograsso/Documents/Sentiance/tools/scraper/scraped_site"
    KEYWORDS_INDEX = "SALIDA.json"
    
    mo.md("# 🔍 Sentiance SDK JSON Analyzer")
    return OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DOCS_DIR, KEYWORDS_INDEX, mo, json, os, Path, requests, re


@app.cell
def __(OPENROUTER_API_KEY, OPENROUTER_BASE_URL, requests):
    """LLM API caller."""

    # Model selection - CHANGE THIS TO SAVE MONEY
    # MODEL = "google/gemini-2.0-flash-exp:free"  # FREE!
    MODEL = "qwen/qwen-2.5-72b-instruct"      # $0.35/1M (best paid)
    # MODEL = "mistralai/mistral-small"         # $0.20/1M (cheapest)
    # MODEL = "meta-llama/llama-3.1-8b-instruct:free"  # FREE
    
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
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    return call_llm,


@app.cell
def __(KEYWORDS_INDEX, json):
    """Load keyword index."""
    
    with open(KEYWORDS_INDEX, 'r') as f:
        keyword_index = json.load(f)
    
    print(f"✅ Loaded keyword index: {len(keyword_index)} files")
    print(f"📝 Sample: {list(keyword_index.items())[:2]}")
    
    return keyword_index,


@app.cell
def __(DOCS_DIR, Path, call_llm, json, keyword_index, re):
    """Main analyzer class."""
    
    class SentianceAnalyzer:
        def __init__(self, keyword_index: dict, docs_dir: str):
            self.keyword_index = keyword_index
            self.docs_dir = docs_dir
            self._file_cache = {}
        
        def analyze_json(self, json_obj: dict, view: str = "programmer") -> dict:
            """
            Full pipeline: JSON → keyword match → select docs → analyze
            """
            
            # Step 1: Extract keywords from JSON
            json_keywords = self._extract_json_keywords(json_obj)
            print(f"🔑 JSON keywords: {json_keywords}")
            
            # Step 2: LLM picks best files from keyword index
            selected_files = self._llm_select_files(json_obj, json_keywords)
            print(f"📄 Selected files: {selected_files}")
            
            # Step 3: Read selected files
            docs_content = self._read_files(selected_files)
            print(f"📖 Read {len(docs_content)} files ({sum(len(v) for v in docs_content.values())} chars)")
            
            # Step 4: LLM final analysis
            analysis = self._llm_analyze(json_obj, docs_content, view)
            
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

Select TOP 3-4 MOST RELEVANT files for analyzing this JSON.
Prioritize files whose keywords match the JSON fields.

Return ONLY a JSON array of filenames:
["filename1.md", "filename2.md", "filename3.md"]

No explanations, just the JSON array.
"""
            
            response = call_llm(prompt, max_tokens=512)
            
            # Extract JSON array
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                selected = json.loads(json_match.group())
                return selected[:4]  # Max 4 files
            
            return []
        
        def _read_files(self, filenames: list) -> dict:
            """Read selected documentation files."""
            docs_content = {}
            
            for filename in filenames:
                filepath = Path(self.docs_dir) / filename
                
                if not filepath.exists():
                    print(f"⚠️  File not found: {filename}")
                    continue
                
                if filename not in self._file_cache:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # Read first 3000 chars per file
                        self._file_cache[filename] = f.read()[:3000]
                
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

DOCUMENTACIÓN REAL DE SENTIANCE (extraída de los archivos):

{self._format_docs(docs_content)}

Basado en la DOCUMENTACIÓN REAL anterior, proporciona un análisis detallado.
Usa un formato claro con encabezados y viñetas.
"""
            
            response = call_llm(prompt, max_tokens=2048)
            return response
        
        def _format_docs(self, docs_content: dict) -> str:
            """Format docs for LLM prompt."""
            formatted = []
            for filename, content in docs_content.items():
                formatted.append(f"### File: {filename}\n{content}\n")
            return "\n".join(formatted)
    
    # Initialize analyzer
    analyzer = SentianceAnalyzer(keyword_index, DOCS_DIR)
    
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
    """Display input."""
    json_input
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
def __(analyze_btn, analyzer, json, json_input, mo, view_selector):
    import traceback
    import time
    
    # This cell ONLY triggers when the run_button is clicked
    ts = time.strftime("%H:%M:%S")
    
    if analyze_btn.value:
        print(f"[{ts}] ⚡ REACTIVITY TRIGGERED: Analysis starting...")
        
        try:
            raw_input = json_input.value.strip()
            if not raw_input:
                 print(f"[{ts}] ⚠️ Input empty.")
                 rendered_output = mo.md("⚠️ **Please provide some JSON data**")
            else:
                json_obj = json.loads(raw_input)
                print(f"[{ts}] 📝 JSON Parsed. Calling Analyzer...")
                
                with mo.status.spinner(title="Contacting AI...") as status_box:
                    result = analyzer.analyze_json(json_obj, view=view_selector.value)
                    
                    print(f"[{ts}] ✅ LLM returned result.")
                    rendered_output = mo.md(f"""
### ✅ Analysis Complete (at {ts})

**Keywords:** {', '.join(result['json_keywords'][:8])}
**Docs Used:** {', '.join(result['selected_files'])}

---

{result['analysis']}
""")
                 
        except json.JSONDecodeError as e:
            print(f"[{ts}] ❌ JSON Error: {e}")
            rendered_output = mo.md(f"❌ **Invalid JSON**: {e}")
        except Exception as e:
            print(f"[{ts}] ❌ Critical Error: {e}")
            rendered_output = mo.vstack([
                mo.md(f"❌ **Error**: {e}"),
                mo.accordion({"Technical Traceback": mo.md(f"```python\n{traceback.format_exc()}\n```")})
            ])
        finally:
            print(f"[{ts}] 🏁 Analysis cell execution finished.")
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

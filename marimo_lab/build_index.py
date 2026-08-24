# build_index.py
"""
One-time script: Build keyword index from all documentation files.
Run: python build_index.py docs/ keywords.json
"""

import json
import os
from pathlib import Path
import requests
from typing import Dict, List
import re
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modelo. Precios por millon de tokens y contexto, verificados contra el
# catalogo de OpenRouter el 2026-08-11. Los IDs caducan: cuando un modelo se
# retira la API responde 404, no 401, asi que un 404 aca casi nunca es la clave.
# Catalogo vigente: https://openrouter.ai/api/v1/models
#
# Esta tarea lee documentos enteros y devuelve 10 palabras clave, asi que pesa
# el precio de entrada y el tamano de contexto, no el de salida.
#
MODEL = "google/gemini-2.5-flash-lite"     # $0.10 ent / $0.40 sal - contexto 1M
# MODEL = "google/gemini-2.5-flash"        # $0.30 ent / $2.50 sal - contexto 1M
# MODEL = "qwen/qwen-2.5-72b-instruct"     # $0.36 ent / $0.40 sal - contexto 32K

def call_openrouter(prompt: str, model: str = MODEL) -> str:
    """Call OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # El codigo distingue la causa, que si no es facil de confundir:
        # 404 es el modelo, no la credencial.
        causas = {
            401: "clave invalida o ausente en marimo_lab/.env",
            402: "credito agotado en la cuenta de OpenRouter",
            404: (f"el modelo '{model}' no existe o fue retirado; "
                  "consulta https://openrouter.ai/api/v1/models"),
            429: "limite de peticiones alcanzado; reintenta en unos segundos",
        }
        causa = causas.get(response.status_code)
        if causa:
            raise requests.exceptions.HTTPError(
                f"OpenRouter {response.status_code}: {causa}", response=response
            ) from e
        raise

    return response.json()["choices"][0]["message"]["content"]

def extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response."""
    # Try to find JSON block
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return {}

def build_keyword_index(docs_dir: str, output_path: str = "keywords.json"):
    """
    Build keyword index for all documentation files.
    LLM reads each file and extracts relevant keywords.
    """
    
    all_files = list(Path(docs_dir).glob("*.md"))
    print(f"📚 Found {len(all_files)} documentation files")
    
    keyword_index = {}
    
    # Process in batches of 5 files
    batch_size = 5
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i+batch_size]
        
        # Read file contents
        files_content = {}
        for filepath in batch:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Read first 2000 chars (enough for keyword extraction)
                content = f.read()[:2000]
                files_content[filepath.name] = content
        
        # Ask LLM to extract keywords
        prompt = f"""
Extract the Source URL and TOP 10 KEYWORDS for each documentation file below.
Each file starts with "Source: <URL>".

For each file, return an array where:
1. The FIRST element is the absolute URL found after "Source: ".
2. The remaining elements are technical keywords (class names, method names, fields, SDK concepts).

Files and their content (first 2000 chars):
{json.dumps(files_content, indent=2)}

Return ONLY valid JSON (no markdown, no explanations):
{{
  "filename1.md": ["https://docs.sentiance.com/...", "keyword1", "keyword2", ...],
  "filename2.md": ["https://docs.sentiance.com/...", "keyword1", "keyword2", ...]
}}

Focus on technical terms, API names, and domain concepts.
"""
        
        print(f"🤖 Processing batch {i//batch_size + 1}/{(len(all_files)-1)//batch_size + 1}...")
        
        try:
            response = call_openrouter(prompt)
            batch_keywords = extract_json_from_response(response)
            keyword_index.update(batch_keywords)
            print(f"   ✅ Indexed {len(batch_keywords)} files")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(keyword_index, f, indent=2)
    
    print(f"\n✅ Keyword index saved to {output_path}")
    print(f"📊 Total files indexed: {len(keyword_index)}")
    
    # Show sample
    print("\n📝 Sample keywords:")
    for filename, keywords in list(keyword_index.items())[:3]:
        print(f"  {filename}: {keywords[:5]}...")
    
    return keyword_index

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python build_index.py <docs_directory> [output_json]")
        sys.exit(1)
    
    docs_dir = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "keywords.json"
    
    # Check API key
    if not OPENROUTER_API_KEY:
        print("❌ Set OPENROUTER_API_KEY in .env file")
        sys.exit(1)
    
    build_keyword_index(docs_dir, output_path)

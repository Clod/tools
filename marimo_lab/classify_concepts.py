# classify_concepts.py
"""
Script to classify documentation files as "Conceptual" or "Reference".
Conceptual files will be included in every RAG analysis for better grounding.
"""

import json
import os
from pathlib import Path
import requests
import re
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model selection
MODEL = "google/gemini-2.0-flash-001"

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
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]

def extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response."""
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return {}

def classify_documentation(docs_dir: str, output_path: str = "concepts.json"):
    """
    Classify documentation files into "CONCEPTUAL" or "REFERENCE".
    """
    
    all_files = list(Path(docs_dir).glob("*.md"))
    print(f"📚 Analyzing {len(all_files)} files for conceptual content...")
    
    conceptual_files = []
    
    # Process in batches of 10 files (classification is lighter than keyword extraction)
    batch_size = 10
    total_batches = (len(all_files) + batch_size - 1) // batch_size
    
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i+batch_size]
        
        # Read file contents
        files_summary = {}
        for filepath in batch:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Read first 1500 chars for classification
                content = f.read()[:1500]
                files_summary[filepath.name] = content
        
        prompt = f"""
Classify each Sentiance SDK documentation file as either "CONCEPTUAL" or "REFERENCE".

- **CONCEPTUAL**: 
    - Theory, core logic behavior, and high-level definitions (e.g., "How detection works", "What is an event?", "Understanding Timeline").
    - **EXCLUDE**: "How-to" guides, simple set up steps, platform-specific code snippets.
- **REFERENCE**: 
    - Integration guides (Android/iOS setup), API Reference, release notes, typical "Usage" or "Getting Started" if it's just code steps.
    - Specific configuration details (permissions, gradle, plist).

Files to classify:
{json.dumps(files_summary, indent=2)}

Return ONLY valid JSON:
{{
  "filename1.md": "CONCEPTUAL",
  "filename2.md": "REFERENCE",
  ...
}}
"""
        
        print(f"🤖 Classifying batch {i//batch_size + 1}/{total_batches}...")
        
        try:
            response = call_openrouter(prompt)
            batch_classification = extract_json_from_response(response)
            
            for fname, classification in batch_classification.items():
                if classification == "CONCEPTUAL":
                    conceptual_files.append(fname)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Save conceptual list
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(conceptual_files), f, indent=2)
    
    print(f"\n✅ Found {len(conceptual_files)} conceptual files. Saved to {output_path}")
    return conceptual_files

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python classify_concepts.py <docs_directory> [output_json]")
        sys.exit(1)
    
    docs_dir = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "concepts.json"
    
    if not OPENROUTER_API_KEY:
        print("❌ Set OPENROUTER_API_KEY in .env file")
        sys.exit(1)
    
    classify_documentation(docs_dir, output_path)

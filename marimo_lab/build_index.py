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

# Model selection - CHANGE THIS TO SAVE MONEY
# MODEL = "google/gemini-2.0-flash-exp:free"  # FREE!
MODEL = "qwen/qwen-2.5-72b-instruct"      # $0.35/1M (best paid)
# MODEL = "mistralai/mistral-small"         # $0.20/1M (cheapest)
# MODEL = "meta-llama/llama-3.1-8b-instruct:free"  # FREE

def call_openrouter(prompt: str, model: str = MODEL) -> str:
    """Call OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
    response.raise_for_status()
    
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
Extract TOP 10 KEYWORDS for each documentation file below.
Keywords should be: class names, method names, field names, event types, SDK concepts.

Files and their content (first 2000 chars):
{json.dumps(files_content, indent=2)}

Return ONLY valid JSON (no markdown, no explanations):
{{
  "filename1.md": ["keyword1", "keyword2", "keyword3", ...],
  "filename2.md": ["keyword1", "keyword2", ...]
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

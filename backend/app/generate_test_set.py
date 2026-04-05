"""
generate_test_set.py — Synthetic Data Generation Engine.
Automates the creation of professional test datasets from uploaded documents.
"""

import asyncio
import json
import os
import random
from typing import List, Dict
from groq import AsyncGroq
from app.core.config import settings
from app.services.vector_store import get_all_chunks
from app.core.logger import logger

# Initialize Groq client
_client = AsyncGroq(api_key=settings.groq_api_key)

_SYNTHETIC_PROMPT = """
You are a highly skilled AI testing engineer. Your task is to generate a professional testing pair (Question and Ground Truth) based on the provided document chunk.

ROLES:
1. QUESTION: Should be natural, slightly complex, and specific. Avoid saying "Based on the text...". Ask it as if a real user is seeking information.
2. GROUND TRUTH: Should be a perfect, comprehensive answer that directly answers the question using ONLY the provided context.

DOCUMENT CHUNK:
{chunk_text}

OUTPUT FORMAT:
Return ONLY a valid JSON object in this format:
{{
  "question": "The question here",
  "ground_truth": "The perfect answer here"
}}
"""

async def generate_synthetic_test_set(num_questions: int = 10, source: str = None):
    print("\n" + "="*60)
    print("🧠  Distributed AI - Synthetic Test Data Generator")
    print("="*60)
    
    # 1. Fetch available chunks from vector store
    print(f"📂 Fetching document chunks...")
    chunks = get_all_chunks(source=source)
    
    if not chunks:
        print("❌ No documents found in Knowledge Base. Upload a document first!")
        return

    print(f"📝 Found {len(chunks)} potential sources. Selecting top candidates...")
    
    # Select a diverse set of chunks (avoid duplicates if possible)
    # We'll take chunks that are at least 300 chars long to ensure they have enough content
    candidates = [c for c in chunks if len(c['text']) > 300]
    if len(candidates) < num_questions:
        candidates = chunks
        
    selected_chunks = random.sample(candidates, min(len(candidates), num_questions))
    
    test_set = []
    
    print(f"🤖 Generating {len(selected_chunks)} synthetic test cases via LLM...")
    
    for i, chunk in enumerate(selected_chunks):
        try:
            print(f"  [{i+1}/{len(selected_chunks)}] Synthesizing from: {chunk['source']}...")
            
            response = await _client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional QA engineer."},
                    {"role": "user", "content": _SYNTHETIC_PROMPT.format(chunk_text=chunk['text'])}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            test_set.append({
                "question": data.get("question"),
                "ground_truth": data.get("ground_truth"),
                "metadata": {
                    "source_chunk": chunk['source'],
                    "auto_generated": True,
                    "timestamp": str(os.path.getctime(__file__)) # just a marker
                }
            })
            
        except Exception as e:
            print(f"  ⚠️ Error generating question {i+1}: {e}")
            continue

    # 2. Save results to test_set.json
    output_path = os.path.join("app", "test_set.json")
    with open(output_path, 'w') as f:
        json.dump(test_set, f, indent=2)

    print(f"\n" + "="*60)
    print(f"✅ SUCCESS: {len(test_set)} synthetic test cases generated!")
    print(f"📁 Dataset saved to: backend/{output_path}")
    print("="*60 + "\n")
    print("💡 Next Step: Run 'python -m app.run_evaluation' to test your AI against this new data.")

if __name__ == "__main__":
    asyncio.run(generate_synthetic_test_set(num_questions=5))

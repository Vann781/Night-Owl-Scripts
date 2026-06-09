import os
import re
import time
import pickle
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types
import pdfplumber
import numpy as np

load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PDF_PATH       = "document.pdf"
CHUNK_SIZE     = 800    # bigger chunks = fewer API calls
CHUNK_OVERLAP  = 50
CACHE_FILE     = "embeddings_cache.pkl"

client = genai.Client(api_key=GEMINI_API_KEY)

# ── STEP 1: EXTRACT TEXT FROM PDF ──────────────────────────────
def extract_text(pdf_path: str) -> str:
    print(f"📄 Reading {pdf_path}...")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        print(f"   ✅ Extracted {len(text):,} characters from {len(pdf.pages)} pages")
    return text

# ── STEP 2: SPLIT INTO CHUNKS ───────────────────────────────────
def split_into_chunks(text: str, size: int, overlap: int) -> list:
    print(f"✂️  Splitting into chunks (size={size}, overlap={overlap})...")
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end]

        if end < len(text):
            last_period = chunk.rfind('. ')
            if last_period > size * 0.5:
                chunk = chunk[:last_period + 1]

        chunks.append(chunk.strip())
        step = max(len(chunk) - overlap, 1)
        start += step

    print(f"   ✅ Created {len(chunks)} chunks")
    return chunks

# ── STEP 3: EMBED CHUNKS ────────────────────────────────────────
def embed_single(text: str) -> list:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return result.embeddings[0].values

def embed_texts(texts: list) -> list:
    print(f"🔢 Embedding {len(texts)} chunks with Gemini...")
    embeddings = []

    for i, text in enumerate(texts):
        try:
            embedding = embed_single(text)
            embeddings.append(embedding)
            time.sleep(0.7)  # stay under 100 req/min free tier limit

        except Exception as e:
            if '429' in str(e):
                print(f"   ⏳ Rate limit hit at chunk {i+1}, waiting 60s...")
                time.sleep(60)
                # retry
                embedding = embed_single(text)
                embeddings.append(embedding)
            else:
                raise e

        if (i + 1) % 5 == 0 or (i + 1) == len(texts):
            print(f"   {i+1}/{len(texts)} done...")

    print(f"   ✅ All chunks embedded ({len(embeddings[0])} dimensions each)")
    return embeddings

# ── STEP 4: COSINE SIMILARITY ───────────────────────────────────
def cosine_similarity(a, b) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ── STEP 5: FIND RELEVANT CHUNKS ────────────────────────────────
def retrieve(query: str, chunks: list, chunk_embeddings: list, top_k: int = 4) -> list:
    query_result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    query_embedding = query_result.embeddings[0].values

    scores = [cosine_similarity(query_embedding, ce) for ce in chunk_embeddings]
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    top_chunks = [chunks[i] for i in top_indices]

    print(f"\n🔍 Top {top_k} chunks found (scores: {[round(scores[i], 3) for i in top_indices]})")
    return top_chunks

# ── STEP 6: ANSWER WITH GEMINI ──────────────────────────────────
def answer(query: str, context_chunks: list) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""You are a helpful assistant. Answer the user's question using ONLY the context below.
If the answer is not in the context, say "I couldn't find that in the document."
Do not make up information.
if the user says thankyou or smemthing simimilar to it , reaply him welcome politely.

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )
    return response.text

# ── MAIN ────────────────────────────────────────────────────────
def main():
    if Path(CACHE_FILE).exists():
        print("⚡ Loading cached embeddings (skipping re-embedding)...")
        with open(CACHE_FILE, "rb") as f:
            chunks, chunk_embeddings = pickle.load(f)
        print(f"   ✅ Loaded {len(chunks)} chunks from cache")
    else:
        if not Path(PDF_PATH).exists():
            print(f"❌ PDF not found: {PDF_PATH}")
            print(f"   Place your PDF in the same folder and name it '{PDF_PATH}'")
            return

        text = extract_text(PDF_PATH)
        chunks = split_into_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)
        chunk_embeddings = embed_texts(chunks)

        with open(CACHE_FILE, "wb") as f:
            pickle.dump((chunks, chunk_embeddings), f)
        print("💾 Embeddings cached — next run will be instant\n")

    print("\n" + "="*50)
    print("💬 RAG Chatbot ready! Ask anything about your document.")
    print("   Type 'quit' to exit | 'clear' to reset cache")
    print("="*50 + "\n")

    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() == 'quit':
            print("👋 Bye!")
            break
        if query.lower() == 'clear':
            Path(CACHE_FILE).unlink(missing_ok=True)
            print("🗑️  Cache cleared. Restart to re-embed.")
            break

        relevant_chunks = retrieve(query, chunks, chunk_embeddings)
        response = answer(query, relevant_chunks)
        print(f"\n🤖 Bot: {response}\n")

if __name__ == "__main__":
    main()
"""
test_chunking.py
Run this from the backend/ directory to verify chunking + FAISS are working:
    python test_chunking.py
"""

import os
import time
import requests
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ── 0. Load API key from .env ────────────────────────────────────────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

if not api_key:
    print("[ERROR] No API key found in .env file. Please add SEMANTIC_SCHOLAR_API_KEY=your_key")
    exit()

# ── 1. Fetch papers with pagination ──────────────────────────────────────────
print("\n" + "="*60)
print("STEP 1: Fetching papers from Semantic Scholar API...")
print("="*60)

papers = []
for offset in range(0, 20, 3):  # fetch 20 papers in batches of 3
    response = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": "transformer attention neural network",
            "fields": "title,abstract,citationCount,year",
            "limit": 3,
            "offset": offset,
        },
        headers={"x-api-key": api_key},
        timeout=15,
    )
    if response.status_code == 200:
        batch = [p for p in response.json().get("data", []) if p.get("abstract")]
        papers.extend(batch)
        print(f"[OK] Batch {offset//3+1}: {len(batch)} papers with abstracts")
    else:
        print(f"[ERROR] API call failed: {response.status_code} {response.text}")
        break

    time.sleep(1)  # respect 1/sec API limit

if not papers:
    print("[ERROR] No papers with abstracts returned. Try a different query.")
    exit()

print(f"\n[OK] Total papers collected: {len(papers)}\n")

for i, p in enumerate(papers):
    print(f"  Paper {i+1}: {p.get('title', 'N/A')}")
    print(f"           Year: {p.get('year')} | Citations: {p.get('citationCount', 0)}")
    abstract = p.get("abstract") or ""
    print(f"           Abstract length: {len(abstract)} characters\n")

# ── 2. Chunk the abstracts ────────────────────────────────────────────────────
print("="*60)
print("STEP 2: Chunking abstracts with RecursiveCharacterTextSplitter")
print("        chunk_size=500, chunk_overlap=100")
print("="*60)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
)

all_chunks = []
for p in papers:
    abstract = p.get("abstract")
    title    = p.get("title", "Unknown")
    chunks   = text_splitter.create_documents(
        texts=[abstract],
        metadatas=[{"title": title, "year": p.get("year"), "citations": p.get("citationCount", 0)}]
    )
    print(f"\n  📄 '{title[:55]}...'")
    print(f"     Abstract: {len(abstract)} chars → split into {len(chunks)} chunk(s)")
    for j, chunk in enumerate(chunks):
        print(f"     Chunk {j+1}: {len(chunk.page_content)} chars | "
              f"Preview: \"{chunk.page_content[:80].strip()}...\"")
    all_chunks.extend(chunks)

print(f"\n✅ Total chunks created: {len(all_chunks)}")

# ── 3. Embed and index into FAISS ─────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 3: Loading HuggingFace embeddings + building FAISS index...")
print("        model: sentence-transformers/all-mpnet-base-v2")
print("="*60)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
faiss_store = FAISS.from_documents(all_chunks, embeddings)

print(f"[OK] FAISS index built in RAM with {len(all_chunks)} vectors")

# ── 4. Run a semantic search ──────────────────────────────────────────────────
# ── 4. Run interactive semantic search ───────────────────────────────────────
print("\n" + "="*60)
print("STEP 4: Interactive semantic search on FAISS index")
print("="*60)

while True:
    query = input("\nEnter your query (or type 'exit' to quit): ")
    if query.lower() in ["exit", "quit"]:
        print("\n[OK] Exiting semantic search loop.")
        break

    results = faiss_store.similarity_search(query, k=5)

    print(f"\nTop {len(results)} most relevant chunks:\n")
    for i, doc in enumerate(results):
        meta = doc.metadata
        print(f"Result {i+1}:")
        print(f"  Source    : '{meta.get('title', 'Unknown')[:55]}...'")
        print(f"  Year/Cite : {meta.get('year')} | {meta.get('citations', 0)} citations")
        print(f"  Content   : \"{doc.page_content[:150].strip()}...\"\n")

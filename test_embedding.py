"""Quick smoke-test for the HuggingFace embedding + FAISS retrieval pipeline.

Run from the project root:
    python test_embedding.py

Requires HF_API_TOKEN to be set in your environment or .env file.
"""

from dotenv import load_dotenv
load_dotenv()

from propra.retrieval.rag import get_embedding, retriever

QUERY = "Brauche ich eine Baugenehmigung?"

# ── 1. Embedding ────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"Query: {QUERY}")
print(f"{'='*60}")

print("\n[1] Calling get_embedding()...")
embedding = get_embedding(QUERY)

print(f"    Type     : {type(embedding)}")
print(f"    Length   : {len(embedding)}  (expected 384)")
print(f"    First 5  : {[round(v, 6) for v in embedding[:5]]}")

if len(embedding) != 384:
    print("    ❌ FAIL — unexpected embedding length")
else:
    print("    ✅ PASS — embedding length is 384")

# ── 2. FAISS retrieval ──────────────────────────────────────────────────────
print(f"\n[2] Running FAISS retrieval (top 5)...")
try:
    results = retriever.retrieve(QUERY, k=5)
except FileNotFoundError as e:
    print(f"    ❌ FAISS index not found: {e}")
    raise SystemExit(1)

if not results:
    print("    ❌ No results returned")
else:
    print(f"    ✅ {len(results)} result(s) returned\n")
    for i, r in enumerate(results, 1):
        print(f"  --- Result {i} ---")
        print(f"  Jurisdiction : {r['jurisdiction_label']} ({r['jurisdiction']})")
        print(f"  Paragraph    : {r['source_paragraph']}")
        print(f"  Score        : {r['score']:.4f}")
        print(f"  Text preview : {r['text'][:200].strip()}...")
        print()

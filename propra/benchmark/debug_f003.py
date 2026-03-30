"""Debug script for F003: inspect FAISS chunk format vs KG node format.

Loads chunks.pkl and graph.pkl, prints field examples for the first
Brandenburg FAISS chunks and the first KG nodes, and attempts to match
a Brandenburg chunk to a graph node by source_paragraph.

Usage:
    python -m propra.benchmark.debug_f003
"""

import re
import sys
import pickle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import joblib  # noqa: E402
from propra.retrieval.rag import Chunk  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

_PROPRA_DIR = Path(__file__).resolve().parents[1]
_CHUNKS_PATH = _PROPRA_DIR / "retrieval" / "chunks.pkl"
_GRAPH_PATH = _PROPRA_DIR / "data" / "graph.pkl"

# ---------------------------------------------------------------------------
# 1. chunks.pkl — first 5 Brandenburg chunks
# ---------------------------------------------------------------------------

print("=" * 60)
print("CHUNKS.PKL — first 5 DE-BB chunks")
print("=" * 60)

class _ChunkUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == "Chunk":
            return Chunk
        return super().find_class(module, name)

with open(_CHUNKS_PATH, "rb") as f:
    chunks = _ChunkUnpickler(f).load()

bb_chunks = [c for c in chunks if getattr(c, "jurisdiction", None) == "DE-BB"
             or (isinstance(c, dict) and c.get("jurisdiction") == "DE-BB")]

if not bb_chunks:
    print("WARNING: no DE-BB chunks found")
else:
    for i, c in enumerate(bb_chunks[:5]):
        if isinstance(c, dict):
            chunk_id = c.get("chunk_id", "<missing>")
            source_paragraph = c.get("source_paragraph", "<missing>")
            source_file = c.get("source_file", "<missing>")
        else:
            chunk_id = getattr(c, "chunk_id", "<missing>")
            source_paragraph = getattr(c, "source_paragraph", "<missing>")
            source_file = getattr(c, "source_file", "<missing>")
        print(f"  [{i}] chunk_id:         {chunk_id}")
        print(f"       source_paragraph:  {source_paragraph}")
        print(f"       source_file:       {source_file}")

first_bb = bb_chunks[0] if bb_chunks else None
if first_bb is not None:
    if isinstance(first_bb, dict):
        faiss_sp = first_bb.get("source_paragraph", "<missing>")
    else:
        faiss_sp = getattr(first_bb, "source_paragraph", "<missing>")
    print()
    print(f"FAISS source_paragraph format: {faiss_sp!r}")

# ---------------------------------------------------------------------------
# 2. graph.pkl — first 10 node IDs + attribute keys on first node
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("GRAPH.PKL — first 10 nodes")
print("=" * 60)

graph = joblib.load(_GRAPH_PATH)

# Support both networkx Graph and plain dict/list formats
if hasattr(graph, "nodes"):
    # NetworkX graph
    node_ids = list(graph.nodes)[:10]
    print(f"Graph type: {type(graph).__name__}  |  total nodes: {graph.number_of_nodes()}")
    for nid in node_ids:
        print(f"  node_id: {nid!r}")
    if node_ids:
        first_node_id = node_ids[0]
        attrs = graph.nodes[first_node_id]
        print()
        print(f"Attribute keys on first node ({first_node_id!r}):")
        for k, v in attrs.items():
            preview = str(v)[:80]
            print(f"  {k}: {preview!r}")
        print()
        print(f"KG node_id format: {first_node_id!r}")
elif isinstance(graph, dict):
    node_ids = list(graph.keys())[:10]
    print(f"Graph type: dict  |  total keys: {len(graph)}")
    for nid in node_ids:
        print(f"  key: {nid!r}")
    if node_ids:
        first_node_id = node_ids[0]
        first_val = graph[first_node_id]
        print()
        print(f"Value type on first key ({first_node_id!r}): {type(first_val).__name__}")
        if isinstance(first_val, dict):
            for k, v in first_val.items():
                preview = str(v)[:80]
                print(f"  {k}: {preview!r}")
        print()
        print(f"KG node_id format: {first_node_id!r}")
else:
    print(f"Graph type: {type(graph).__name__} — no .nodes or dict interface")
    print("KG node_id format: <unknown>")

# ---------------------------------------------------------------------------
# 3. Attempt source_paragraph match for first Brandenburg chunk
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("MATCH ATTEMPT — first DE-BB chunk vs KG nodes")
print("=" * 60)

if first_bb is None:
    print("No DE-BB chunk available — skipping match attempt")
else:
    if hasattr(graph, "nodes"):
        # (a) exact match: node_id == source_paragraph
        match_a = faiss_sp in graph.nodes
        print(f"(a) node_id == source_paragraph ({faiss_sp!r}): {match_a}")

        # (b) exact match: node attribute source_paragraph == faiss_sp
        match_b_node = None
        for nid in graph.nodes:
            attrs = graph.nodes[nid]
            if attrs.get("source_paragraph") == faiss_sp:
                match_b_node = nid
                break
        if match_b_node is not None:
            print(f"(b) node with source_paragraph == {faiss_sp!r}: found -> {match_b_node!r}")
        else:
            print(f"(b) node with source_paragraph == {faiss_sp!r}: not found")

        # Sample a few node IDs near any that contain the paragraph prefix
        prefix = faiss_sp.split("_")[0] if "_" in faiss_sp else faiss_sp[:10]
        candidates = [nid for nid in list(graph.nodes)[:200] if prefix in str(nid)]
        if candidates:
            print(f"    Nodes containing prefix {prefix!r}: {candidates[:5]}")
    elif isinstance(graph, dict):
        match_a = faiss_sp in graph
        print(f"(a) dict key == source_paragraph ({faiss_sp!r}): {match_a}")

        match_b_key = None
        for k, v in graph.items():
            if isinstance(v, dict) and v.get("source_paragraph") == faiss_sp:
                match_b_key = k
                break
        if match_b_key is not None:
            print(f"(b) key with source_paragraph == {faiss_sp!r}: found -> {match_b_key!r}")
        else:
            print(f"(b) key with source_paragraph == {faiss_sp!r}: not found")
    else:
        print("Graph format not recognised — skipping match")

print("=" * 60)
print("F003 FIX VALIDATION — derived node ID lookup")
print("=" * 60)

def _chunk_to_node_id(chunk):
    sp = chunk.get("source_paragraph", "")
    sf = chunk.get("source_file", "")
    if not sp or not sf:
        return None
    m = re.match(r"(?:§\s*|Art\.\s*)(\d+\w*)", sp.strip())
    if not m:
        return None
    section = m.group(1)
    return f"{sf}_§{section}"

bb_chunks = [c for c in chunks if c.jurisdiction == "DE-BB"][:5]
hits = 0
for c in bb_chunks:
    node_id = _chunk_to_node_id(vars(c) if hasattr(c, '__dict__') else c)
    found = node_id in graph.nodes if node_id else False
    status = "HIT" if found else "MISS"
    print(f"  [{status}] {c.source_paragraph[:50]!r:55} -> {node_id}")
    if found:
        hits += 1
print(f"Result: {hits}/5 nodes found in graph")

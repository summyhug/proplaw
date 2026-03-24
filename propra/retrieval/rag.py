"""
FAISS-based RAG pipeline for Propra.

Three responsibilities:
  1. Chunking  — split LBO .txt files by § paragraph, attach jurisdiction +
                 source_paragraph metadata extracted from the filename.
  2. Indexing  — embed chunks with sentence-transformers, build a FAISS
                 IndexFlatIP index and persist it to propra/retrieval/.
  3. Retrieval — embed a query, return top-k chunks with metadata.

Usage (CLI):
    python rag.py build          # chunk all txt/ files, embed, save index
    python rag.py query "..."    # query the saved index

Usage (import):
    from rag import retriever
    results = retriever.retrieve("Abstandsfläche Bayern", k=5)
"""

from __future__ import annotations

import sys
import re
import pickle
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import faiss as _faiss_mod
    from sentence_transformers import SentenceTransformer as _ST

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent        # propra/retrieval/
TXT_DIR = _THIS_DIR.parent / "data" / "txt"        # propra/data/txt/
RETRIEVAL_DIR = _THIS_DIR                          # propra/retrieval/
INDEX_PATH = RETRIEVAL_DIR / "faiss.index"
CHUNKS_PATH = RETRIEVAL_DIR / "chunks.pkl"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_MIN_CHARS = 80          # skip stubs shorter than this
CHUNK_MAX_CHARS = 1200        # hard cap — split overlength paragraphs

# ---------------------------------------------------------------------------
# Jurisdiction map — filename stem -> ISO 3166-2 code + human label
# ---------------------------------------------------------------------------

JURISDICTION_MAP: dict[str, dict] = {
    "BauO_BE":   {"code": "DE-BE", "label": "Berlin"},
    "BauO_HE":   {"code": "DE-HE", "label": "Hessen"},
    "BauO_LSA":  {"code": "DE-ST", "label": "Sachsen-Anhalt"},
    "BauO_MV":   {"code": "DE-MV", "label": "Mecklenburg-Vorpommern"},
    "BauO_NRW":  {"code": "DE-NW", "label": "Nordrhein-Westfalen"},
    "BayBO":     {"code": "DE-BY", "label": "Bayern"},
    "BbgBO":     {"code": "DE-BB", "label": "Brandenburg"},
    "HBauO":     {"code": "DE-HH", "label": "Hamburg"},
    "LBO_HB":    {"code": "DE-HB", "label": "Bremen"},
    "LBO_SH":    {"code": "DE-SH", "label": "Schleswig-Holstein"},
    "LBO_SL":    {"code": "DE-SL", "label": "Saarland"},
    "LBauO_RLP": {"code": "DE-RP", "label": "Rheinland-Pfalz"},
    "MBO":       {"code": "DE-MBO", "label": "Musterbauordnung"},
    "NBauO":     {"code": "DE-NI", "label": "Niedersachsen"},
    "SaechsBO":  {"code": "DE-SN", "label": "Sachsen"},
    "ThuerBO":   {"code": "DE-TH", "label": "Thüringen"},
    "BauO_BW":   {"code": "DE-BW", "label": "Baden-Württemberg"},
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """A single retrievable unit — one § paragraph from one LBO."""
    chunk_id: str          # e.g. "DE-BW_§6_0"
    jurisdiction: str      # ISO 3166-2, e.g. "DE-BW"
    jurisdiction_label: str  # human label, e.g. "Baden-Württemberg"
    source_file: str       # stem of the originating .txt file
    source_paragraph: str  # e.g. "§ 6" or "Art. 6" (Bayern)
    text: str              # full paragraph text


# ---------------------------------------------------------------------------
# 1. Chunker
# ---------------------------------------------------------------------------

# Matches § 6, § 6a, § 16a at line-start (standard LBOs).
# Matches Art. 6, Art. 6a anywhere in the line (BayBO style: headers appear
# inline after the previous paragraph, e.g. "...sein. Art. 4 Bebauung...").
# Cross-references (Art. 27 Abs. 2, Art. 2 Nr. 2, Art. 3 Satz 1) are excluded
# via negative lookahead on the first word following the article number.
_PARA_PATTERN = re.compile(
    r"(?:(?:^|\n)\s*(?=§)"
    r"|(?<!\w)(?=Art\.\s*\d+\w*\s+(?!Abs\b|Nr\b|Satz\b)[A-ZÄÖÜ]))"
    r"((?:§+\s*\d+\w*|Art\.\s*\d+\w*)(?:\s+[A-ZÄÖÜ][^\n]{0,120})?)",
)


def _split_long_chunk(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """Split a paragraph that exceeds max_chars on sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    while len(text) > max_chars:
        split_at = text.rfind(".", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        parts.append(text[: split_at + 1].strip())
        text = text[split_at + 1 :].strip()
    if text:
        parts.append(text)
    return parts


def chunk_file(txt_path: Path) -> list[Chunk]:
    """
    Parse a single LBO .txt file into Chunk objects.

    Strategy: split on § / Art. paragraph headers. Each paragraph header
    plus its body text becomes one chunk. Overlength chunks are split on
    sentence boundaries.
    """
    stem = txt_path.stem
    jur = JURISDICTION_MAP.get(stem)
    if jur is None:
        print(f"WARNING: no jurisdiction mapping for '{stem}' — skipping")
        return []

    raw = txt_path.read_text(encoding="utf-8", errors="replace")

    # Split into (header, body) pairs
    matches = list(_PARA_PATTERN.finditer(raw))
    chunks: list[Chunk] = []

    for i, match in enumerate(matches):
        header = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        body = raw[start:end].strip()
        full_text = f"{header}\n{body}".strip()

        if len(full_text) < CHUNK_MIN_CHARS:
            continue
        # Filter 1: TOC dot-leader lines (e.g. "§ 80 ... 155")
        if "......" in full_text:
            continue
        # Filter 2: cross-reference / navigation lines — two § references in the
        # text with no real Absatz content in the body.
        # HBauO synopsis format: "§ N TitleHH § M TitleMBO" with the header regex
        # eating both headers as one group (they fit in the 120-char window) and
        # the body left empty.  Guard: if body starts with "(" it is real law
        # content (an Absatz marker) and must be kept regardless.
        if (len(re.findall(r"§\s*\d+", full_text)) >= 2
                and not re.match(r"^\(", body.strip())):
            continue

        for part_idx, part in enumerate(_split_long_chunk(full_text)):
            # Normalise header to first token for chunk_id
            para_token = re.sub(r"\s+", "_", header.split("\n")[0])[:30]
            chunk_id = f"{jur['code']}_{para_token}_{part_idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    jurisdiction=jur["code"],
                    jurisdiction_label=jur["label"],
                    source_file=stem,
                    source_paragraph=header.split("\n")[0],
                    text=part,
                )
            )

    return chunks


def chunk_all(txt_dir: Path = TXT_DIR) -> list[Chunk]:
    """Chunk every .txt file in txt_dir. Returns combined list."""
    all_chunks: list[Chunk] = []
    txt_files = sorted(txt_dir.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {txt_dir}")
    for f in txt_files:
        file_chunks = chunk_file(f)
        print(f"  {f.name}: {len(file_chunks)} chunks")
        all_chunks.extend(file_chunks)
    print(f"Total chunks: {len(all_chunks)}")
    return all_chunks


# ---------------------------------------------------------------------------
# 2. Indexer
# ---------------------------------------------------------------------------

def build_index(txt_dir: Path = TXT_DIR, retrieval_dir: Path = RETRIEVAL_DIR) -> None:
    """
    Build FAISS index from all LBO txt files and persist to retrieval_dir.

    Saves two files:
      faiss.index  — FAISS IndexFlatIP (inner-product / cosine after normalisation)
      chunks.pkl   — list[Chunk] in the same order as index vectors
    """
    import faiss  # noqa: PLC0415 — deferred to avoid slow startup
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415

    retrieval_dir.mkdir(parents=True, exist_ok=True)

    print("Chunking corpus...")
    chunks = chunk_all(txt_dir)

    print(f"Loading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    print("Embedding chunks (this takes a few minutes)...")
    texts = [c.text for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,   # cosine similarity via inner product
    )
    embeddings = embeddings.astype("float32")

    dim = embeddings.shape[1]
    print(f"Building FAISS IndexFlatIP (dim={dim}, vectors={len(chunks)})...")
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(retrieval_dir / "faiss.index"))
    with open(retrieval_dir / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    print(f"Index saved to {retrieval_dir / 'faiss.index'}")
    print(f"Chunks saved to {retrieval_dir / 'chunks.pkl'}")
    print(f"Done. {index.ntotal} vectors indexed.")


# ---------------------------------------------------------------------------
# 3. Retriever
# ---------------------------------------------------------------------------

class _ChunkUnpickler(pickle.Unpickler):
    """
    Remaps __main__.Chunk → rag.Chunk.

    chunks.pkl is built by running `python rag.py build` directly, which makes
    rag.py the __main__ module. Python's pickle stores the dataclass as
    __main__.Chunk. When the index is loaded from main.py or uvicorn, __main__
    is no longer rag.py, so the default Unpickler raises
    "Can't get attribute 'Chunk'". This subclass redirects the lookup.
    """

    def find_class(self, module: str, name: str):
        if module == "__main__" and name == "Chunk":
            return Chunk
        return super().find_class(module, name)


class Retriever:
    """
    Loads a persisted FAISS index and exposes a retrieve() method.

    Lazy-loads on first call so importing rag.py does not trigger disk I/O.
    """

    def __init__(
        self,
        index_path: Path = INDEX_PATH,
        chunks_path: Path = CHUNKS_PATH,
        model_name: str = EMBED_MODEL,
    ):
        self._index_path = index_path
        self._chunks_path = chunks_path
        self._model_name = model_name
        self._index: _faiss_mod.Index | None = None
        self._chunks: list[Chunk] | None = None
        self._model: _ST | None = None

    def _load(self) -> None:
        if self._index is not None:
            return
        import faiss  # noqa: PLC0415 — deferred to avoid slow startup
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        if not self._index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self._index_path}. "
                "Run: python rag.py build"
            )
        self._index = faiss.read_index(str(self._index_path))
        with open(self._chunks_path, "rb") as f:
            self._chunks = _ChunkUnpickler(f).load()
        self._model = SentenceTransformer(self._model_name)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        jurisdiction: str | None = None,
        node_types: list[str] | None = None,
    ) -> list[dict]:
        """
        Retrieve top-k chunks most relevant to query.

        Args:
            query:        Natural language query (DE or EN).
            k:            Number of results to return.
            jurisdiction: Optional ISO 3166-2 filter, e.g. "DE-BW".
                          When set, only chunks from that state are returned.
            node_types:   Optional list of KG node type hints from goal classification
                          (e.g. ['abstandsflaeche', 'verfahrensfreies_vorhaben']).
                          Appended to the query to improve semantic retrieval precision.

        Returns:
            List of dicts with keys: chunk_id, jurisdiction,
            jurisdiction_label, source_paragraph, text, score.
        """
        self._load()

        # Augment query with node type keywords to steer semantic search
        effective_query = query
        if node_types:
            effective_query = f"{query} {' '.join(node_types)}"

        query_vec = self._model.encode(
            [effective_query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        # Over-fetch when filtering by jurisdiction so we still return k results
        fetch_k = k * 50 if jurisdiction else k
        fetch_k = min(fetch_k, self._index.ntotal)

        scores, indices = self._index.search(query_vec, fetch_k)

        results: list[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self._chunks[idx]
            if jurisdiction and chunk.jurisdiction != jurisdiction:
                continue
            results.append(
                {
                    **asdict(chunk),
                    "score": float(score),
                }
            )
            if len(results) == k:
                break

        return results


# Singleton — import and use directly: from rag import retriever
retriever = Retriever()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_build() -> None:
    build_index()


def _cmd_query(query: str, k: int = 5, jurisdiction: str | None = None) -> None:
    results = retriever.retrieve(query, k=k, jurisdiction=jurisdiction)
    if not results:
        print("No results found.")
        return
    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} | {r['jurisdiction_label']} | {r['source_paragraph']} | score={r['score']:.4f}")
        print(r["text"][:400] + ("..." if len(r["text"]) > 400 else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: python rag.py build | python rag.py query <text> [k] [jurisdiction]")
        sys.exit(1)

    cmd = args[0]
    if cmd == "build":
        _cmd_build()
    elif cmd == "query":
        if len(args) < 2:
            print("Usage: python rag.py query <text> [k] [jurisdiction]")
            sys.exit(1)
        q = args[1]
        k_arg = int(args[2]) if len(args) > 2 else 5
        jur_arg = args[3] if len(args) > 3 else None
        _cmd_query(q, k=k_arg, jurisdiction=jur_arg)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

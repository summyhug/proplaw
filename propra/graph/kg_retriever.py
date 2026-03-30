"""
KG retriever for Propra.

Loads the NetworkX knowledge graph from ``propra/data/graph.pkl`` and exposes
``get_related_chunks()``, which takes FAISS chunk dicts and returns both
KG-derived context and diagnostics describing whether the graph was available
and whether any seed nodes matched.
"""

from __future__ import annotations

import logging
import re

import joblib
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows (cp1252 consoles would otherwise mangle
# German legal text in log messages).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)

_GRAPH_PATH = Path(__file__).parent.parent / "data" / "graph.pkl"

_graph = None
_graph_load_attempted = False
_graph_load_error: str | None = None

_SECTION_REF_RE = re.compile(r"(?:§|Art\.?)\s*\d+[a-z]?", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class KGEnrichmentResult:
    """Diagnostic result for one KG enrichment attempt."""

    status: str
    nodes: list[dict[str, Any]] = field(default_factory=list)
    node_ids: list[str] = field(default_factory=list)
    seed_paragraphs: list[str] = field(default_factory=list)
    message: str | None = None


def _load_graph():
    """Load the graph from disk once and remember the reason when it fails."""
    global _graph, _graph_load_attempted, _graph_load_error
    if _graph_load_attempted:
        return _graph

    _graph_load_attempted = True

    if not _GRAPH_PATH.exists():
        _graph_load_error = f"Graph file not found at {_GRAPH_PATH}"
        logger.warning("%s — KG enrichment disabled.", _graph_load_error)
        return None

    try:
        _graph = joblib.load(_GRAPH_PATH)
        logger.info(
            "KG graph loaded: %d nodes, %d edges",
            _graph.number_of_nodes(),
            _graph.number_of_edges(),
        )
    except Exception as exc:  # noqa: BLE001
        _graph_load_error = f"Failed to load graph from {_GRAPH_PATH}: {exc}"
        logger.warning("%s", _graph_load_error)
        _graph = None

    return _graph


def get_related_chunks(
    faiss_chunks: list[dict[str, Any]],
    hops: int = 2,
    max_per_seed: int = 5,
) -> KGEnrichmentResult:
    """
    Traverse the KG from FAISS-seeded nodes and return context + diagnostics.

    Status values:
      - ``graph_unavailable``: graph file missing or failed to load
      - ``no_seed_match``: graph loaded, but no seed node matched any FAISS chunk
      - ``no_related_nodes``: seed nodes matched, but traversal added no new nodes
      - ``used``: one or more KG nodes were added
    """
    g = _load_graph()
    if g is None:
        return KGEnrichmentResult(
            status="graph_unavailable",
            message=_graph_load_error or "Knowledge graph is unavailable.",
        )

    if not faiss_chunks:
        return KGEnrichmentResult(
            status="no_seed_match",
            message="Knowledge-graph enrichment skipped because FAISS returned no chunks.",
        )

    results: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()
    seed_paragraphs: list[str] = []

    for chunk in faiss_chunks:
        candidate_id = _chunk_to_node_id(chunk)
        if candidate_id is None or candidate_id not in g.nodes:
            continue

        seed_ids = [candidate_id]

        seed_paragraphs.append(chunk.get("source_paragraph", "").strip())

        for seed in seed_ids:
            neighbours = _bfs_neighbours(g, seed, hops=hops, max_nodes=max_per_seed)
            for node_id in neighbours:
                if node_id in seen_node_ids:
                    continue
                seen_node_ids.add(node_id)
                node_data = g.nodes[node_id]
                results.append(_make_context_dict(node_id, node_data))

    unique_seed_paragraphs = sorted(set(seed_paragraphs))

    if not unique_seed_paragraphs:
        return KGEnrichmentResult(
            status="no_seed_match",
            message="Graph loaded, but none of the FAISS source paragraphs matched KG seed nodes.",
        )

    if not results:
        return KGEnrichmentResult(
            status="no_related_nodes",
            seed_paragraphs=unique_seed_paragraphs,
            message=(
                "KG seed nodes matched, but traversal did not add any neighbouring nodes "
                "within the configured hop limit."
            ),
        )

    node_ids = [node["kg_node_id"] for node in results]
    return KGEnrichmentResult(
        status="used",
        nodes=results,
        node_ids=node_ids,
        seed_paragraphs=unique_seed_paragraphs,
        message=(
            f"Added {len(node_ids)} KG nodes from "
            f"{len(unique_seed_paragraphs)} matched FAISS seed paragraphs."
        ),
    )


def _find_seed_ids(g, chunk: dict[str, Any]) -> list[str]:
    """Find graph node IDs that plausibly correspond to one FAISS chunk."""
    chunk_sp = (chunk.get("source_paragraph") or "").strip()
    chunk_jurisdiction = (chunk.get("jurisdiction") or "").strip()
    chunk_jurisdiction_label = (chunk.get("jurisdiction_label") or "").strip()

    seed_ids: list[str] = []
    for node_id, data in g.nodes(data=True):
        if not _same_jurisdiction(chunk_jurisdiction, chunk_jurisdiction_label, data):
            continue
        node_sp = (data.get("source_paragraph") or "").strip()
        if _source_paragraph_matches(chunk_sp, node_sp):
            seed_ids.append(node_id)

    return seed_ids


def _same_jurisdiction(
    chunk_jurisdiction: str,
    chunk_jurisdiction_label: str,
    node_data: dict[str, Any],
) -> bool:
    """Restrict KG seeds to the same jurisdiction when metadata is present."""
    node_jurisdiction = (node_data.get("jurisdiction") or "").strip()
    node_jurisdiction_label = (node_data.get("jurisdiction_label") or "").strip()

    if chunk_jurisdiction and node_jurisdiction:
        return chunk_jurisdiction == node_jurisdiction
    if chunk_jurisdiction_label and node_jurisdiction_label:
        return chunk_jurisdiction_label == node_jurisdiction_label
    return True


def _source_paragraph_matches(chunk_sp: str, node_sp: str) -> bool:
    """Match paragraph references despite formatting differences."""
    if not chunk_sp or not node_sp:
        return False

    norm_chunk = _normalize_text(chunk_sp)
    norm_node = _normalize_text(node_sp)

    if norm_chunk == norm_node:
        return True
    if norm_chunk in norm_node or norm_node in norm_chunk:
        return True

    chunk_refs = _extract_section_refs(norm_chunk)
    node_refs = _extract_section_refs(norm_node)
    return bool(chunk_refs and node_refs and chunk_refs.intersection(node_refs))


def _normalize_text(value: str) -> str:
    """Normalize whitespace and casing for paragraph matching."""
    collapsed = _WHITESPACE_RE.sub(" ", value).strip().lower()
    return collapsed.replace("art ", "art. ")


def _extract_section_refs(value: str) -> set[str]:
    """Extract section tokens like '§ 6' or 'Art. 6' from free text."""
    refs: set[str] = set()
    for match in _SECTION_REF_RE.findall(value):
        refs.add(_WHITESPACE_RE.sub(" ", match).strip().lower())
    return refs


def _chunk_to_node_id(chunk: dict) -> str | None:
    """Derive KG node ID from FAISS chunk metadata.

    FAISS source_paragraph: '§ 7 Nicht überbaute Flächen...'
    FAISS source_file:      'BbgBO'
    Target node ID:         'BbgBO_§7'
    """
    sp = chunk.get("source_paragraph", "")
    sf = chunk.get("source_file", "")
    if not sp or not sf:
        return None
    # Extract section number (handles § 6, § 6a, Art. 6, Art. 6a)
    m = re.match(r"(?:§\s*|Art\.\s*)(\d+\w*)", sp.strip())
    if not m:
        return None
    section = m.group(1)  # e.g. "7" or "6a"
    return f"{sf}_§{section}"  # e.g. "BbgBO_§7"


def _bfs_neighbours(g, start: str, hops: int, max_nodes: int) -> list[str]:
    """Collect up to ``max_nodes`` unique neighbour IDs within ``hops`` steps."""
    visited: set[str] = {start}
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    collected: list[str] = []

    while queue and len(collected) < max_nodes:
        current, depth = queue.popleft()
        if depth >= hops:
            continue

        neighbours = list(g.successors(current)) + list(g.predecessors(current))
        for nb in neighbours:
            if nb in visited:
                continue
            visited.add(nb)
            collected.append(nb)
            if len(collected) >= max_nodes:
                break
            queue.append((nb, depth + 1))

    return collected


def _make_context_dict(node_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build the standardised context dict from a graph node."""
    jurisdiction = data.get("jurisdiction") or ""
    jurisdiction_label = data.get("jurisdiction_label") or jurisdiction
    return {
        "text": data.get("text") or "",
        "source_paragraph": data.get("source_paragraph") or "",
        "jurisdiction": jurisdiction,
        "jurisdiction_label": jurisdiction_label,
        "kg_source": True,
        "kg_node_id": node_id,
    }

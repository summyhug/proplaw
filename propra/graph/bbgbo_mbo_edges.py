"""
Copy MBO section-defined edges onto BbgBO using the BbgBO↔MBO section mapping.

For each MBO edge (source, target, relation), we map MBO § and row ID to BbgBO §
via BbgBO_mbo_mapping.json. We only emit an edge when both mapped BbgBO nodes
exist in the graph (structure-based, best-effort).

Usage:
    Called from build_graph after BbgBO nodes and state_structural_edges are in place.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import networkx as nx

from propra.graph.schema import Edge
from propra.graph.mbo_section_edges import edges as mbo_edges

_DATA = Path(__file__).parent.parent / "data"
_MAPPING_FILE = _DATA / "BbgBO_mbo_mapping.json"

# MBO node ID patterns: MBO_§6_1.1 (content) or MBO_§6 (section anchor)
_MBO_CONTENT_RE = re.compile(r"^MBO_§(\d+[a-z]?)_(.+)$")
_MBO_ANCHOR_RE = re.compile(r"^MBO_§(\d+[a-z]?)$")


def _load_reverse_mapping(mapping_path: Path) -> dict[str, list[str]]:
    """
    Load BbgBO_mbo_mapping.json and build MBO § → [BbgBO §].
    mapping is { "state_para": "mbo_para" } so BbgBO §1 → MBO §1.
    Reverse: mbo_para "1" → ["1"] (BbgBO §§ that map to MBO §1).
    """
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping = data.get("mapping", {})
    reverse: dict[str, list[str]] = {}
    for bbgbo_para, mbo_para in mapping.items():
        reverse.setdefault(str(mbo_para), []).append(str(bbgbo_para))
    return reverse


def _mbo_node_to_bbgbo_candidates(mbo_nid: str, reverse_map: dict[str, list[str]]) -> list[str]:
    """
    Map one MBO node ID to a list of possible BbgBO node IDs (same row ID, BbgBO § from mapping).
    Returns [] if MBO section has no BbgBO mapping.
    """
    m_anchor = _MBO_ANCHOR_RE.match(mbo_nid)
    if m_anchor:
        mbo_sec = m_anchor.group(1)
        bbgbo_paras = reverse_map.get(mbo_sec, [])
        return [f"BbgBO_§{q}" for q in bbgbo_paras]
    m_content = _MBO_CONTENT_RE.match(mbo_nid)
    if m_content:
        mbo_sec, row_id = m_content.group(1), m_content.group(2)
        bbgbo_paras = reverse_map.get(mbo_sec, [])
        return [f"BbgBO_§{q}_{row_id}" for q in bbgbo_paras]
    return []


def bbgbo_edges_from_mbo(
    G: nx.DiGraph,
    prefix: str = "BbgBO_",
    mapping_path: Optional[Path] = None,
) -> list[Edge]:
    """
    Build BbgBO edges by copying MBO section edges via the section mapping.

    For each MBO edge (src, tgt, relation), we map src and tgt to BbgBO node IDs.
    We only add an edge when both mapped nodes exist in G. When multiple BbgBO
    sections map to the same MBO section, we take the first matching pair so that
    both nodes exist (prefer same section when source and target are in same MBO §).

    Args:
        G: The graph (must already contain BbgBO nodes).
        prefix: Node ID prefix for the state (e.g. BbgBO_).
        mapping_path: Path to {STATE}_mbo_mapping.json. Defaults to data/BbgBO_mbo_mapping.json.

    Returns:
        List of Edge objects to add (only where both endpoints exist).
    """
    path = mapping_path or _MAPPING_FILE
    if not path.exists():
        return []
    reverse_map = _load_reverse_mapping(path)
    law_name = prefix.rstrip("_")
    out: list[Edge] = []
    for e in mbo_edges():
        src_candidates = _mbo_node_to_bbgbo_candidates(e.source, reverse_map)
        tgt_candidates = _mbo_node_to_bbgbo_candidates(e.target, reverse_map)
        if not src_candidates or not tgt_candidates:
            continue
        # Prefer same-section when both are in one BbgBO § (e.g. content → anchor in same §)
        added = False
        for src_nid in src_candidates:
            if src_nid not in G:
                continue
            for tgt_nid in tgt_candidates:
                if tgt_nid not in G:
                    continue
                # sourced_from: § number from source node (e.g. BbgBO_§6_1.1 → §6)
                sec = src_nid.split("§")[1].split("_")[0] if "§" in src_nid else ""
                out.append(
                    Edge(
                        source=src_nid,
                        target=tgt_nid,
                        relation=e.relation,
                        sourced_from=f"§{sec} {law_name}" if sec else law_name,
                        metadata={
                            "reasoning": "Structure inherited from MBO; same relation type.",
                            "mbo_edge": f"{e.source} → {e.target}",
                        },
                    )
                )
                added = True
                break
            if added:
                break
    return out

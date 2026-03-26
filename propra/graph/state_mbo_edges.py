"""
Copy MBO section-defined edges onto any state graph via a state↔MBO section mapping.

This generalises the old BbgBO-only projector. For each MBO edge we map the source
and target section to the state's mapped section and keep the same row ID when a
matching state node exists.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import networkx as nx

from propra.graph.mbo_section_edges import edges as mbo_edges
from propra.graph.schema import Edge

_DATA = Path(__file__).parent.parent / "data"

# MBO node ID patterns: MBO_§6_1.1 (content) or MBO_§6 (section anchor)
_MBO_CONTENT_RE = re.compile(r"^MBO_§(\d+[a-z]?)_(.+)$")
_MBO_ANCHOR_RE = re.compile(r"^MBO_§(\d+[a-z]?)$")


def mapping_path_for_state(state: str) -> Path:
    """Return the default mapping path for a state name, e.g. BayBO."""
    return _DATA / f"{state}_mbo_mapping.json"


def _load_reverse_mapping(mapping_path: Path) -> dict[str, list[str]]:
    """
    Load {STATE}_mbo_mapping.json and build MBO § → [STATE §].

    The JSON mapping stores {state_para: mbo_para}. Reverse it so one MBO section can
    map to one or more state sections.
    """
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping = data.get("mapping", {})
    reverse: dict[str, list[str]] = {}
    for state_para, mbo_para in mapping.items():
        reverse.setdefault(str(mbo_para), []).append(str(state_para))
    return reverse


def _mbo_node_to_state_candidates(mbo_nid: str, prefix: str, reverse_map: dict[str, list[str]]) -> list[str]:
    """
    Map one MBO node ID to possible state node IDs with the same row ID.

    Examples:
      MBO_§6        -> BayBO_§6
      MBO_§6_5.3    -> BayBO_§6_5.3
    """
    m_anchor = _MBO_ANCHOR_RE.match(mbo_nid)
    if m_anchor:
        mbo_sec = m_anchor.group(1)
        state_paras = reverse_map.get(mbo_sec, [])
        return [f"{prefix}§{q}" for q in state_paras]

    m_content = _MBO_CONTENT_RE.match(mbo_nid)
    if m_content:
        mbo_sec, row_id = m_content.group(1), m_content.group(2)
        state_paras = reverse_map.get(mbo_sec, [])
        return [f"{prefix}§{q}_{row_id}" for q in state_paras]

    return []


def state_edges_from_mbo(
    G: nx.DiGraph,
    prefix: str,
    mapping_path: Optional[Path] = None,
) -> list[Edge]:
    """
    Build state edges by copying MBO section edges via the state↔MBO section mapping.

    Only edges whose mapped source and target both exist in the state subgraph are emitted.
    """
    state = prefix.rstrip("_")
    path = mapping_path or mapping_path_for_state(state)
    if not path.exists():
        return []

    reverse_map = _load_reverse_mapping(path)
    if not reverse_map:
        return []

    out: list[Edge] = []
    for e in mbo_edges():
        src_candidates = _mbo_node_to_state_candidates(e.source, prefix, reverse_map)
        tgt_candidates = _mbo_node_to_state_candidates(e.target, prefix, reverse_map)
        if not src_candidates or not tgt_candidates:
            continue

        added = False
        for src_nid in src_candidates:
            if src_nid not in G:
                continue
            for tgt_nid in tgt_candidates:
                if tgt_nid not in G:
                    continue
                sec = src_nid.split("§", 1)[1].split("_", 1)[0] if "§" in src_nid else ""
                out.append(
                    Edge(
                        source=src_nid,
                        target=tgt_nid,
                        relation=e.relation,
                        sourced_from=f"§{sec} {state}" if sec else state,
                        metadata={
                            "reasoning": "Structure inherited from MBO via section mapping.",
                            "mbo_edge": f"{e.source} -> {e.target}",
                        },
                    )
                )
                added = True
                break
            if added:
                break
    return out

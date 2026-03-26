"""Backward-compatible Brandenburg wrapper around the generic state MBO edge projector."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import networkx as nx

from propra.graph.schema import Edge
from propra.graph.state_mbo_edges import state_edges_from_mbo

_DATA = Path(__file__).parent.parent / "data"
_MAPPING_FILE = _DATA / "BbgBO_mbo_mapping.json"


def bbgbo_edges_from_mbo(
    G: nx.DiGraph,
    prefix: str = "BbgBO_",
    mapping_path: Optional[Path] = None,
) -> list[Edge]:
    """Build BbgBO edges by copying MBO section edges via the section mapping."""
    return state_edges_from_mbo(G, prefix=prefix, mapping_path=mapping_path or _MAPPING_FILE)

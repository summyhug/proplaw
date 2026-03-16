"""
Extracts cross-references from node text and yields 'references' edges.

Parses legal text for patterns like "§ 34", "§6 Abs. 1", "§§ 5–7" and creates
references edges from the citing node to the anchor node of the cited paragraph.
This adds intersectional links across the graph (e.g. §34 Treppen citing §6).

Usage:
    from propra.graph.references_edges import references_edges
    for edge in references_edges(G):
        add_edge(G, edge)
"""

import re
from collections import defaultdict

import networkx as nx

from propra.graph.schema import Edge


# § 34, §34, § 6 Absatz 1, §§ 5–7, § 16a
# Also matches BayBO-style "Art. 34", "Art. 6a"
_PARA_RE = re.compile(
    r"(?:§§?|Art\.)\s*(\d+[a-z]?)\s*(?:[\-–]\s*(\d+[a-z]?))?"
)

def _parse_paragraph_refs(text: str) -> set[str]:
    """Extract cited § numbers from text. Returns set of normalized keys like '34', '6', '16a'."""
    if not text or not isinstance(text, str):
        return set()
    refs = set()
    for m in _PARA_RE.finditer(text):
        g1, g2 = m.group(1), m.group(2)
        if g1:
            refs.add(g1.lower())
            if g2:
                try:
                    a = int(re.sub(r"[a-z]", "", g1))
                    b = int(re.sub(r"[a-z]", "", g2))
                    for i in range(a, min(b + 1, a + 25)):
                        refs.add(str(i))
                except ValueError:
                    refs.add(g2.lower())
    return refs


def _node_prefix(nid: str) -> str | None:
    """Return inventory prefix from node ID (e.g. 'MBO', 'BbgBO', 'BW_LBO', 'BayBO') for same-law reference grouping."""
    if nid.startswith("BW_LBO_"):
        return "BW_LBO"
    if nid.startswith("MBO_"):
        return "MBO"
    if nid.startswith("BbgBO_"):
        return "BbgBO"
    if nid.startswith("BayBO_"):
        return "BayBO"
    return None


def _source_para_to_key(source_paragraph: str) -> str | None:
    """Extract § number key from source_paragraph, e.g. '§5 LBO BW' -> '5', '§34 MBO' -> '34'."""
    if not source_paragraph:
        return None
    m = re.search(r"§\s*(\d+[a-z]?)", source_paragraph, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _build_para_anchors(G: nx.DiGraph) -> dict[tuple[str, str], str]:
    """
    Map (prefix, §_num) -> anchor node ID (first non-zahlenwert node in that section).
    """
    by_key: dict[tuple[str, str], list[str]] = defaultdict(list)
    for nid, data in G.nodes(data=True):
        prefix = _node_prefix(nid)
        if not prefix:
            continue
        sp = data.get("source_paragraph", "")
        key = _source_para_to_key(sp)
        if not key:
            continue
        by_key[(prefix, key)].append(nid)

    anchors = {}
    for (prefix, key), nids in by_key.items():
        # Prefer non-zahlenwert; then sort by id and take first
        with_type = [(nid, G.nodes[nid].get("type")) for nid in nids]
        non_zw = [nid for nid, t in with_type if t != "zahlenwert"]
        candidates = sorted(non_zw) if non_zw else sorted(nids)
        anchors[(prefix, key)] = candidates[0]
    return anchors


def references_edges(G: nx.DiGraph) -> list[Edge]:
    """
    For each node, parse its text for § references and return references edges
    to the anchor of the cited paragraph (same inventory only).
    """
    anchors = _build_para_anchors(G)
    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()

    for nid, data in G.nodes(data=True):
        prefix = _node_prefix(nid)
        if not prefix:
            continue
        text = data.get("text", "")
        refs = _parse_paragraph_refs(text)
        sp = data.get("source_paragraph", "")
        self_key = _source_para_to_key(sp)
        for ref in refs:
            if ref == self_key:
                continue
            target = anchors.get((prefix, ref))
            if not target or target == nid:
                continue
            pair = (nid, target)
            if pair in seen:
                continue
            seen.add(pair)
            edges.append(
                Edge(
                    source=nid,
                    target=target,
                    relation="references",
                    sourced_from=sp,
                    metadata={"reasoning": f"Text cites §{ref}."},
                )
            )
    return edges

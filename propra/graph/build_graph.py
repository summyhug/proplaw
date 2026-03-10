"""
Unified Propra knowledge graph builder.

Builds a single graph.pkl containing all nodes and domain edges:
  1. MBO nodes  — shared federal model code base layer (DE-MBO)
  2. BW nodes   — Baden-Württemberg state rules (DE-BW)
  3. Structural edges — every node connects to its section anchor
  4. Fence domain edges — setback, boundary, permit-free fence rules
  5. References edges — parsed from node text (§ 34, §§ 5–7) for intersectional links

Cross-jurisdiction `state_version_of` edges link BW nodes back to the MBO
nodes they deviate from. References edges connect sections that cite each other.

Usage:
    python -m propra.graph.build_graph
"""

from collections import defaultdict
from pathlib import Path

import networkx as nx

from propra.graph.builder import add_edge, add_node, create_graph, graph_summary, save_graph
from propra.graph.parse_inventory import parse_inventory
from propra.graph.visualize import export_graphml
import propra.graph.fence_edges as fence
from propra.graph.references_edges import references_edges

_DATA = Path(__file__).parent.parent / "data"

_MBO_INVENTORY = str(_DATA / "MBO_node_inventory.md")
_BW_INVENTORY  = str(_DATA / "BW_LBO_node_inventory.md")
_GRAPH_PATH    = str(_DATA / "graph.pkl")
_GRAPHML_PATH  = str(_DATA / "graph.graphml")


def _add_structural_edges(G: nx.DiGraph) -> int:
    """
    Add 'supplements' edges so every node in each section connects to its anchor.

    Nodes are grouped by (source_paragraph, group). Within each group the first
    non-zahlenwert node (alphabetically by ID) becomes the anchor, and all other
    nodes get exactly one supplements edge to it. So we add (n-1) edges per
    group with n nodes — no duplicate links. These are marked as structural
    (metadata["structural"] = True) so they can be filtered from semantic
    "supplements" (e.g. in visualization or when querying domain logic).
    """
    groups: dict[tuple, list[str]] = defaultdict(list)

    for nid, data in G.nodes(data=True):
        src_para = data.get("source_paragraph", "")
        group    = data.get("group", "")
        groups[(src_para, group)].append(nid)

    added = 0
    for (src_para, _), node_ids in groups.items():
        if len(node_ids) < 2:
            continue
        sorted_ids = sorted(node_ids)
        anchor = next(
            (nid for nid in sorted_ids if G.nodes[nid].get("type") != "zahlenwert"),
            sorted_ids[0],
        )
        for nid in sorted_ids:
            if nid == anchor or G.has_edge(nid, anchor):
                continue
            G.add_edge(
                nid, anchor,
                relation="supplements",
                sourced_from=src_para,
                structural=True,  # so UI/queries can treat these separately from domain supplements
            )
            added += 1

    return added


def _load_inventory(path: str, label: str) -> list:
    """Parse an inventory file and return its nodes, printing a summary line."""
    nodes = parse_inventory(path=path)
    print(f"  {label}: {len(nodes)} nodes")
    return nodes


def _apply_edges(G: nx.DiGraph, edge_list: list, label: str) -> None:
    """Add domain edges to the graph, printing a summary line."""
    failed = 0
    for edge in edge_list:
        try:
            add_edge(G, edge)
        except (ValueError, KeyError) as e:
            print(f"    [WARN] {edge.source} → {edge.target}: {e}")
            failed += 1
    status = f"({failed} failed)" if failed else "ok"
    print(f"  {label}: {len(edge_list)} edges  {status}")


def build() -> nx.DiGraph:
    """Build the complete unified knowledge graph and save it."""
    print("=== Propra — Knowledge Graph Build ===\n")

    G = create_graph()

    # 1. Load all nodes
    print("Loading nodes:")
    all_nodes = (
        _load_inventory(_MBO_INVENTORY, "MBO")
        + _load_inventory(_BW_INVENTORY, "BW LBO")
    )
    failed_nodes = 0
    for node in all_nodes:
        try:
            add_node(G, node)
        except ValueError as e:
            print(f"    [ERROR] {node.id}: {e}")
            failed_nodes += 1

    # 2. Structural edges (connect every node to its section anchor)
    structural = _add_structural_edges(G)
    print(f"\nStructural edges: {structural} supplements added")

    # 3. Domain edges (semantic relations between rules)
    print("\nDomain edges:")
    _apply_edges(G, fence.edges(), "fence (BW)")
    # Intersectional: references extracted from node text (e.g. "§ 34", "§§ 5–7")
    ref_edges = references_edges(G)
    _apply_edges(G, ref_edges, "references (from text)")

    # 4. Summary
    summary = graph_summary(G)
    orphans = sum(1 for n in G.nodes if G.degree(n) == 0)
    print(f"\n{'─' * 45}")
    print(f"Nodes     : {summary['node_count']}  (failed: {failed_nodes})")
    print(f"Edges     : {summary['edge_count']}")
    print(f"Orphans   : {orphans}")
    print(f"\nNode types:")
    for t, count in sorted(summary["node_types"].items(), key=lambda x: -x[1]):
        print(f"  {t:<40} {count}")
    print(f"\nRelation types:")
    for r, count in sorted(summary["relation_types"].items(), key=lambda x: -x[1]):
        print(f"  {r:<30} {count}")

    save_graph(G, _GRAPH_PATH)
    export_graphml(G, _GRAPHML_PATH)
    return G


if __name__ == "__main__":
    build()

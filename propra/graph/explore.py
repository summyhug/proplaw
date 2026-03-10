"""
Interactive terminal explorer for the Propra knowledge graph.

Type a node ID (or part of one) to see its attributes and all connected nodes.
No Gephi required.

Usage:
    python -m propra.graph.explore                        # uses graph_fence.pkl
    python -m propra.graph.explore propra/data/graph_base.pkl
"""

import sys
from pathlib import Path

from propra.graph.builder import load_graph

_DEFAULT_GRAPH = str(Path(__file__).parent.parent / "data" / "graph.pkl")


def _print_node(G, nid: str) -> None:
    data = G.nodes[nid]
    print(f"\n{'─' * 60}")
    print(f"  ID          : {nid}")
    print(f"  type        : {data.get('type', '')}")
    print(f"  jurisdiction: {data.get('jurisdiction', '')}")
    print(f"  source      : {data.get('source_paragraph', '')}")
    text = data.get("text", "")
    print(f"  text        : {text[:120]}{'…' if len(text) > 120 else ''}")
    if data.get("numeric_value") not in (None, ""):
        print(f"  value       : {data['numeric_value']} {data.get('unit', '')}")
    if data.get("context"):
        print(f"  context     : {data['context']}")

    # Outgoing edges (this node → target)
    out_edges = list(G.out_edges(nid, data=True))
    if out_edges:
        print(f"\n  ──▶ Outgoing ({len(out_edges)}):")
        for _, target, edata in out_edges:
            tdata = G.nodes[target]
            ttext = tdata.get("text", "")[:60]
            print(f"      [{edata.get('relation','?'):<22}] → {target}")
            print(f"                               \"{ttext}\"")
            print(f"                               sourced from: {edata.get('sourced_from','')}")

    # Incoming edges (source → this node)
    in_edges = list(G.in_edges(nid, data=True))
    if in_edges:
        print(f"\n  ◀── Incoming ({len(in_edges)}):")
        for source, _, edata in in_edges:
            sdata = G.nodes[source]
            stext = sdata.get("text", "")[:60]
            print(f"      [{edata.get('relation','?'):<22}] ← {source}")
            print(f"                               \"{stext}\"")

    if not out_edges and not in_edges:
        print("\n  (no edges — orphan node)")

    print(f"{'─' * 60}")


def explore(graph_path: str = _DEFAULT_GRAPH) -> None:
    G = load_graph(graph_path)
    node_ids = sorted(G.nodes)

    print(f"\nLoaded {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print("Type a node ID or search term. Press Enter with empty input to list all. Ctrl+C to quit.\n")

    while True:
        try:
            query = input("node > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not query:
            for nid in node_ids:
                print(f"  {nid}")
            continue

        # Exact match
        if query in G:
            _print_node(G, query)
            continue

        # Partial match
        matches = [nid for nid in node_ids if query.lower() in nid.lower()]
        if not matches:
            # Also search node text
            matches = [
                nid for nid in node_ids
                if query.lower() in G.nodes[nid].get("text", "").lower()
            ]

        if len(matches) == 1:
            _print_node(G, matches[0])
        elif matches:
            print(f"\n  {len(matches)} matches:")
            for m in matches[:30]:
                text = G.nodes[m].get("text", "")[:50]
                print(f"    {m:<50}  \"{text}\"")
            if len(matches) > 30:
                print(f"  … and {len(matches) - 30} more")
        else:
            print("  No matches found.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_GRAPH
    explore(path)

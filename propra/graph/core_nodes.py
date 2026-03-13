"""
Lists core nodes (high-connectivity hubs) in the Propra knowledge graph.

Core nodes are either:
  - By total degree: section anchors with many in-edges (structural + semantic)
  - By semantic degree: nodes with many non-structural connections (references, domain edges)

Usage:
    python -m propra.graph.core_nodes
"""

from collections import Counter
from pathlib import Path

from propra.graph.builder import load_graph

_DEFAULT_GRAPH = str(Path(__file__).parent.parent / "data" / "graph.pkl")


def semantic_degree(G, nid: str) -> int:
    """Count edges that are not structural supplements (in or out)."""
    total = 0
    for u, v, d in G.in_edges(nid, data=True):
        if d.get("relation") != "supplements" or not d.get("structural"):
            total += 1
    for u, v, d in G.out_edges(nid, data=True):
        total += 1
    return total


def main() -> None:
    G = load_graph(_DEFAULT_GRAPH)

    # --- By total degree (includes structural) ---
    deg = dict(G.degree())
    top_total = sorted(deg.items(), key=lambda x: -x[1])[:20]

    print("=" * 60)
    print("CORE NODES BY TOTAL DEGREE (structural + semantic)")
    print("=" * 60)
    for nid, d in top_total:
        data = G.nodes[nid]
        in_d = G.in_degree(nid)
        out_d = G.out_degree(nid)
        struct_in = sum(
            1 for u, v, ed in G.in_edges(nid, data=True)
            if ed.get("relation") == "supplements" and ed.get("structural")
        )
        print(f"\n{d:3} total (in={in_d:2}, out={out_d})  {nid}")
        print(f"    {data.get('source_paragraph', '')}  [{data.get('type', '')}]")
        print(f"    in-edges: {struct_in} structural supplements, {in_d - struct_in} other (references/domain)")

    # --- By semantic degree only ---
    sem = {nid: semantic_degree(G, nid) for nid in G.nodes()}
    top_sem = sorted(sem.items(), key=lambda x: -x[1])[:15]
    top_sem = [(n, s) for n, s in top_sem if s > 0]

    print("\n" + "=" * 60)
    print("CORE NODES BY SEMANTIC CONNECTIONS ONLY (no structural)")
    print("=" * 60)
    for nid, d in top_sem:
        data = G.nodes[nid]
        in_other = [
            (u, ed.get("relation"))
            for u, v, ed in G.in_edges(nid, data=True)
            if not ed.get("structural")
        ]
        out_edges = [(v, ed.get("relation")) for u, v, ed in G.out_edges(nid, data=True)]
        rels_in = Counter(r for _, r in in_other)
        rels_out = Counter(r for _, r in out_edges)
        print(f"\n{nid}  semantic degree: {d}")
        print(f"    {data.get('source_paragraph', '')}  [{data.get('type', '')}]")
        print(f"    In:  {dict(rels_in)}  <- {[u[:36] for u, _ in in_other[:5]]}")
        print(f"    Out: {dict(rels_out)}  -> {[v[:36] for v, _ in out_edges[:5]]}")


if __name__ == "__main__":
    main()

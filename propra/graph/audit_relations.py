"""
Audit graph relations: sample and review edges to check they make sense.

Use this to run through the dataset systematically by relation type, with
optional sampling and export for spreadsheet review.

Usage:
    # Summary: counts per relation type
    python -m propra.graph.audit_relations

    # Sample 15 edges per relation type (skip structural supplements by default)
    python -m propra.graph.audit_relations --sample 15

    # Focus on one relation type, show 30 examples
    python -m propra.graph.audit_relations --relation references --sample 30

    # Include structural edges in the audit
    python -m propra.graph.audit_relations --sample 10 --include-structural

    # Export all non-structural edges to CSV for review in Excel/Sheets
    python -m propra.graph.audit_relations --export audit_edges.csv

    # Export only 'references' edges with full context
    python -m propra.graph.audit_relations --relation references --export refs.csv
"""

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from propra.graph.builder import load_graph

_DEFAULT_GRAPH = str(Path(__file__).parent.parent / "data" / "graph.pkl")


def _text_preview(text: str, max_len: int = 80) -> str:
    if not text:
        return ""
    t = (text or "").replace("\n", " ").strip()
    return (t[: max_len] + "…") if len(t) > max_len else t


def _get_edges_by_relation(G, include_structural: bool = False):
    """Yield (source, target, edge_data) for each edge, optionally skipping structural supplements."""
    for u, v, d in G.edges(data=True):
        if not include_structural and d.get("relation") == "supplements" and d.get("structural"):
            continue
        yield u, v, d


def run_audit(
    graph_path: str = _DEFAULT_GRAPH,
    relation_filter: str | None = None,
    sample_per_type: int | None = None,
    include_structural: bool = False,
    export_path: str | None = None,
    seed: int = 42,
) -> None:
    G = load_graph(graph_path)
    random.seed(seed)

    edges_by_rel: dict[str, list[tuple]] = defaultdict(list)
    for u, v, d in _get_edges_by_relation(G, include_structural):
        rel = d.get("relation", "?")
        if relation_filter and rel != relation_filter:
            continue
        edges_by_rel[rel].append((u, v, d))

    if not edges_by_rel:
        print("No edges match the filter.")
        return

    # Summary
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    if not include_structural:
        print("(Structural supplements excluded for clarity.)")
    print()
    print("Edges by relation type:")
    for rel in sorted(edges_by_rel.keys(), key=lambda r: -len(edges_by_rel[r])):
        print(f"  {rel:<25} {len(edges_by_rel[rel]):>5}")
    print()

    if export_path:
        _export_csv(G, edges_by_rel, export_path)
        print(f"Exported to {export_path}")
        return

    # Sample and print for review
    sample_n = sample_per_type or 0
    for rel in sorted(edges_by_rel.keys()):
        list_edges = edges_by_rel[rel]
        if sample_n > 0:
            list_edges = random.sample(list_edges, min(sample_n, len(list_edges)))
        print("=" * 70)
        print(f"  RELATION: {rel}  ({len(list_edges)} shown of {len(edges_by_rel[rel])} total)")
        print("=" * 70)
        for u, v, d in list_edges:
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            src_para = d.get("sourced_from", "")
            print(f"  {u}")
            print(f"    --[{rel}]-->  {v}")
            print(f"    source_para: {src_para}")
            print(f"    FROM text: {_text_preview(u_data.get('text', ''), 100)}")
            print(f"    TO   text: {_text_preview(v_data.get('text', ''), 100)}")
            if d.get("metadata", {}).get("reasoning"):
                print(f"    reasoning:   {d['metadata']['reasoning'][:120]}")
            print()
        print()


def _export_csv(G, edges_by_rel: dict, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "relation", "source_id", "target_id", "sourced_from",
            "source_paragraph", "target_paragraph", "source_type", "target_type",
            "source_text_preview", "target_text_preview",
        ])
        for rel, list_edges in sorted(edges_by_rel.items()):
            for u, v, d in list_edges:
                u_data = G.nodes[u]
                v_data = G.nodes[v]
                w.writerow([
                    rel,
                    u, v,
                    d.get("sourced_from", ""),
                    u_data.get("source_paragraph", ""),
                    v_data.get("source_paragraph", ""),
                    u_data.get("type", ""),
                    v_data.get("type", ""),
                    _text_preview(u_data.get("text", ""), 200),
                    _text_preview(v_data.get("text", ""), 200),
                ])


def main() -> None:
    from collections import defaultdict  # noqa: F811

    parser = argparse.ArgumentParser(description="Audit graph relations: sample or export edges for review.")
    parser.add_argument("graph", nargs="?", default=_DEFAULT_GRAPH, help="Path to graph.pkl")
    parser.add_argument("--relation", "-r", dest="relation_filter", help="Only this relation type (e.g. references)")
    parser.add_argument("--sample", "-s", type=int, default=0, help="Sample N edges per relation type to print")
    parser.add_argument("--include-structural", action="store_true", help="Include structural supplements in audit")
    parser.add_argument("--export", "-e", dest="export_path", help="Export edges to CSV file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    args = parser.parse_args()

    run_audit(
        graph_path=args.graph,
        relation_filter=args.relation_filter or None,
        sample_per_type=args.sample,
        include_structural=args.include_structural,
        export_path=args.export_path,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

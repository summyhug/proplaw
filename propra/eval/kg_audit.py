"""
Structural audit of the Propra knowledge graph.

Runs four checks against graph.pkl and prints a pass/fail report:

  1. Coverage     — every registered law has the expected number of section anchors
  2. Orphans      — nodes with zero edges (should be near zero)
  3. References   — every 'references' edge points to a real, existing node
  4. Type audit   — unknown / missing node types flagged per law

Usage:
    python -m propra.eval.kg_audit
    python -m propra.eval.kg_audit --graph propra/data/graph.pkl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from propra.graph.builder import load_graph
from propra.graph.schema import NODE_TYPES

_DEFAULT_GRAPH = Path(__file__).parent.parent / "data" / "graph.pkl"

# Expected minimum section anchors per law (based on law structure).
# A law with fewer anchors than its minimum is almost certainly broken.
_EXPECTED_ANCHORS: dict[str, int] = {
    "BbgBO": 80,
    "BayBO": 90,
    "NBauO": 88,
    "BauO_BE": 95,
    "BauO_HE": 90,
    "BauO_NRW": 78,
    "BauO_LSA": 90,
    "BauO_MV": 90,
    "HBauO": 92,
    "LBO_SH": 88,
    "LBO_SL": 80,
    "LBauO_RLP": 95,
    "SaechsBO": 90,
    "ThuerBO": 95,
}

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"
_WARN = "  [WARN]"


def _law_prefixes(G) -> list[str]:
    """Return all distinct law prefixes present in the graph (e.g. BbgBO, BauO_BE)."""
    prefixes: set[str] = set()
    for nid in G.nodes:
        idx = nid.find("_§")
        if idx > 0:
            prefixes.add(nid[:idx])
    # exclude ROOT and MBO (empty)
    return sorted(p for p in prefixes if p not in {"MBO"})


def check_coverage(G) -> list[str]:
    """
    Check 1: every registered law has at least the expected number of section anchors.
    An anchor node has type 'gesetz' or its ID matches PREFIX_§N with no sub-index.
    """
    results = []
    results.append("CHECK 1 — Section anchor coverage")

    for prefix in _law_prefixes(G):
        # Anchors: nodes matching PREFIX_§N (no dot in the suffix)
        anchors = [
            n for n in G.nodes
            if n.startswith(f"{prefix}_§") and "." not in n.split("_§", 1)[-1]
        ]
        count = len(anchors)
        expected = _EXPECTED_ANCHORS.get(prefix)
        if expected is None:
            results.append(f"{_WARN} {prefix}: {count} anchors (no minimum set)")
        elif count >= expected:
            results.append(f"{_PASS} {prefix}: {count} anchors (≥ {expected})")
        else:
            results.append(f"{_FAIL} {prefix}: only {count} anchors (expected ≥ {expected})")

        # Also report content node count
        content = [n for n in G.nodes if n.startswith(f"{prefix}_§") and "." in n]
        results.append(f"         content nodes: {len(content)}")

    return results


def check_orphans(G) -> list[str]:
    """
    Check 2: nodes with zero edges are almost always a parsing or build error.
    Allowed exceptions: ROOT nodes and MBO nodes (empty corpus).
    """
    results = []
    results.append("CHECK 2 — Orphan nodes (zero edges)")

    for prefix in _law_prefixes(G):
        law_nodes = [n for n in G.nodes if n.startswith(f"{prefix}_")]
        orphans = [
            n for n in law_nodes
            if G.degree(n) == 0 and "ROOT" not in n
        ]
        total = len(law_nodes)
        if not orphans:
            results.append(f"{_PASS} {prefix}: 0 orphans out of {total} nodes")
        elif len(orphans) <= 3:
            results.append(f"{_WARN} {prefix}: {len(orphans)} orphan(s) out of {total}")
            for o in orphans:
                results.append(f"         {o}  text: {G.nodes[o].get('text','')[:60]}")
        else:
            results.append(f"{_FAIL} {prefix}: {len(orphans)} orphans out of {total} nodes")
            for o in orphans[:5]:
                results.append(f"         {o}  text: {G.nodes[o].get('text','')[:60]}")
            if len(orphans) > 5:
                results.append(f"         … and {len(orphans) - 5} more")

    return results


def check_references(G) -> list[str]:
    """
    Check 3: every 'references' edge points to a node that exists in the graph.
    Also flag self-references.
    """
    results = []
    results.append("CHECK 3 — Reference edge integrity")

    dangling: list[tuple[str, str]] = []
    self_refs: list[tuple[str, str]] = []

    for u, v, data in G.edges(data=True):
        if data.get("relation") != "references":
            continue
        if u == v:
            self_refs.append((u, v))
        if v not in G.nodes:
            dangling.append((u, v))

    total_ref = sum(1 for _, _, d in G.edges(data=True) if d.get("relation") == "references")

    if not dangling and not self_refs:
        results.append(f"{_PASS} All {total_ref} references edges point to existing nodes")
    else:
        if dangling:
            results.append(f"{_FAIL} {len(dangling)} dangling references (target missing):")
            for u, v in dangling[:5]:
                results.append(f"         {u} → {v}")
        if self_refs:
            results.append(f"{_WARN} {len(self_refs)} self-references (same source and target):")
            for u, v in self_refs[:3]:
                results.append(f"         {u}")

    # Per-law reference counts
    for prefix in _law_prefixes(G):
        count = sum(
            1 for u, v, d in G.edges(data=True)
            if d.get("relation") == "references" and u.startswith(prefix)
        )
        results.append(f"         {prefix}: {count} outgoing references edges")

    return results


def check_node_types(G) -> list[str]:
    """
    Check 4: all node types must be in the schema's NODE_TYPES set.
    Unknown types suggest classification failures.
    """
    results = []
    results.append("CHECK 4 — Node type validity")

    for prefix in _law_prefixes(G):
        law_nodes = [n for n in G.nodes if n.startswith(f"{prefix}_")]
        unknown: dict[str, list[str]] = {}
        type_counts: dict[str, int] = {}

        for nid in law_nodes:
            t = G.nodes[nid].get("type", "")
            type_counts[t] = type_counts.get(t, 0) + 1
            if t and t not in NODE_TYPES:
                unknown.setdefault(t, []).append(nid)

        missing_type = [n for n in law_nodes if not G.nodes[n].get("type")]

        if not unknown and not missing_type:
            results.append(f"{_PASS} {prefix}: all {len(law_nodes)} nodes have valid types")
        else:
            if unknown:
                results.append(f"{_WARN} {prefix}: {sum(len(v) for v in unknown.values())} nodes with unknown types:")
                for t, nids in sorted(unknown.items()):
                    results.append(f"         type '{t}': {len(nids)} node(s) e.g. {nids[0]}")
            if missing_type:
                results.append(f"{_FAIL} {prefix}: {len(missing_type)} nodes with no type at all")
                for n in missing_type[:3]:
                    results.append(f"         {n}  text: {G.nodes[n].get('text','')[:60]}")

        # Top 5 types for this law
        top = sorted(type_counts.items(), key=lambda x: -x[1])[:5]
        results.append(f"         top types: {', '.join(f'{t}({c})' for t,c in top)}")

    return results


def run_audit(graph_path: Path) -> bool:
    """Run all checks and print results. Returns True if no FAILures."""
    G = load_graph(str(graph_path))
    print(f"\nKnowledge Graph Audit — {graph_path}")
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    all_lines: list[str] = []
    for check_fn in [check_coverage, check_orphans, check_references, check_node_types]:
        lines = check_fn(G)
        all_lines.extend(lines)
        all_lines.append("")

    fail_count = sum(1 for line in all_lines if line.strip().startswith("[FAIL]"))

    for line in all_lines:
        print(line)

    print("─" * 60)
    if fail_count == 0:
        print("  RESULT: PASS — no failures found")
    else:
        print(f"  RESULT: {fail_count} FAILURE(S) — see [FAIL] lines above")

    return fail_count == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Structural audit of the Propra KG")
    parser.add_argument("--graph", type=Path, default=_DEFAULT_GRAPH)
    args = parser.parse_args()

    if not args.graph.exists():
        sys.exit(f"Graph not found: {args.graph}")

    ok = run_audit(args.graph)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

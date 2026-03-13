"""
Audit graph relations: sample and review edges to check they make sense.

Use this to run through the dataset systematically by relation type, with
optional sampling and export for spreadsheet review. Section-by-section
Markdown export gives full text (no terminal truncation) for review in an editor.

Usage:
    # Summary: counts per relation type
    python -m propra.graph.audit_relations

    # Sample 15 edges per relation type (skip structural supplements by default)
    python -m propra.graph.audit_relations --sample 15

    # Write Markdown files by relation type (full text, no truncation) — recommended for audit
    python -m propra.graph.audit_relations --sections-dir propra/data/audit_sections

    # Section by legal paragraph (e.g. §5, §6): one file per paragraph
    python -m propra.graph.audit_relations --sections-dir propra/data/audit_sections --by-paragraph

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
import re
import random
from collections import defaultdict
from pathlib import Path

from propra.graph.builder import load_graph

_DEFAULT_GRAPH = str(Path(__file__).parent.parent / "data" / "graph.pkl")
_DEFAULT_SECTIONS_DIR = str(Path(__file__).parent.parent / "data" / "audit_sections")
_EDGES_PER_FILE = 40  # paginate large relation types into multiple files


def _text_preview(text: str, max_len: int = 80) -> str:
    if not text:
        return ""
    t = (text or "").replace("\n", " ").strip()
    return (t[: max_len] + "…") if len(t) > max_len else t


def _section_slug(name: str) -> str:
    """Safe filename from relation or paragraph (e.g. 'references' or '§5 MBO')."""
    s = (name or "").strip()
    s = re.sub(r"[^\w§\-\.]", "_", s)
    return s.strip("_") or "unknown"


def _paragraph_key(source_paragraph: str) -> str | None:
    """Extract a short key for grouping (e.g. '§5 MBO', '§6 LBO BW')."""
    if not source_paragraph or not source_paragraph.strip():
        return None
    return source_paragraph.strip()


def _write_section_md(
    G,
    out_path: Path,
    title: str,
    edges_list: list[tuple],
    relation_label: str,
    include_structural: bool,
) -> None:
    """Write one Markdown file with full node text for each edge (no truncation)."""
    lines = [
        f"# {title}",
        "",
        f"*{len(edges_list)} edges* · relation: `{relation_label}`",
        "",
        "---",
        "",
    ]
    for i, (u, v, d) in enumerate(edges_list, 1):
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        rel = d.get("relation", "?")
        src_para = d.get("sourced_from", "")
        from_text = (u_data.get("text") or "").strip()
        to_text = (v_data.get("text") or "").strip()
        reasoning = (d.get("metadata") or {}).get("reasoning", "")

        lines.append(f"## Edge {i}")
        lines.append("")
        lines.append(f"- **From:** `{u}`")
        lines.append(f"- **To:** `{v}`")
        lines.append(f"- **Relation:** {rel}")
        lines.append(f"- **Sourced from:** {src_para}")
        lines.append("")
        lines.append("**From (source) node:**")
        lines.append(f"- *source_paragraph:* {u_data.get('source_paragraph', '')}")
        lines.append(f"- *type:* {u_data.get('type', '')}")
        lines.append("")
        lines.append("```")
        lines.append(from_text if from_text else "(no text)")
        lines.append("```")
        lines.append("")
        lines.append("**To (target) node:**")
        lines.append(f"- *source_paragraph:* {v_data.get('source_paragraph', '')}")
        lines.append(f"- *type:* {v_data.get('type', '')}")
        lines.append("")
        lines.append("```")
        lines.append(to_text if to_text else "(no text)")
        lines.append("```")
        if reasoning:
            lines.append("")
            lines.append("*Reasoning:* " + reasoning)
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


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
    sections_dir: str | None = None,
    by_paragraph: bool = False,
    edges_per_file: int = _EDGES_PER_FILE,
    max_edges_per_relation: int | None = None,
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

    # Section-by-section Markdown export (full text, no terminal truncation)
    if sections_dir:
        out_dir = Path(sections_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Optional: only write "small" relation types (few edges) to reduce overwhelm
        rels_to_write = list(edges_by_rel.keys())
        if max_edges_per_relation is not None:
            rels_to_write = [r for r in rels_to_write if len(edges_by_rel[r]) <= max_edges_per_relation]
            if not rels_to_write:
                print(f"No relation types have ≤ {max_edges_per_relation} edges. Writing all.")
                rels_to_write = list(edges_by_rel.keys())
            else:
                print(f"Writing only relation types with ≤ {max_edges_per_relation} edges: {len(rels_to_write)} types.")
        # Sort by edge count (smallest first) so INDEX and START_HERE suggest order
        rels_sorted = sorted(rels_to_write, key=lambda r: len(edges_by_rel[r]))
        index_lines = [
            "# Knowledge graph audit — section by section",
            "",
            "Full node text for each edge (no truncation). Open these files in an editor to review.",
            "",
            "---",
            "",
        ]
        if by_paragraph:
            # Group by source node's source_paragraph
            by_para: dict[str, list[tuple]] = defaultdict(list)
            for rel, list_edges in edges_by_rel.items():
                for edge in list_edges:
                    u, v, d = edge
                    u_data = G.nodes[u]
                    key = _paragraph_key(u_data.get("source_paragraph", ""))
                    if key:
                        by_para[key].append(edge)
            for para in sorted(by_para.keys(), key=lambda p: (p.replace("§", "").replace(" ", ""), p)):
                edges_list = by_para[para]
                slug = _section_slug(para)
                safe = re.sub(r"^§", "par_", slug)
                fname = f"section_{safe}.md"
                out_path = out_dir / fname
                _write_section_md(
                    G, out_path,
                    f"Section: {para}",
                    edges_list,
                    "(mixed relations)",
                    include_structural,
                )
                index_lines.append(f"- [{para}]({fname}) — {len(edges_list)} edges")
            index_lines.append("")
        else:
            # By relation type (optionally paginated); order: smallest first
            for rel in rels_sorted:
                list_edges = edges_by_rel[rel]
                slug = _section_slug(rel)
                n_pages = (len(list_edges) + edges_per_file - 1) // edges_per_file if edges_per_file else 1
                for page in range(n_pages):
                    chunk = list_edges[page * edges_per_file : (page + 1) * edges_per_file]
                    if n_pages > 1:
                        fname = f"{slug}_{page + 1:02d}.md"
                        title = f"Relation: {rel} (page {page + 1}/{n_pages})"
                    else:
                        fname = f"{slug}.md"
                        title = f"Relation: {rel}"
                    out_path = out_dir / fname
                    _write_section_md(G, out_path, title, chunk, rel, include_structural)
                    index_lines.append(f"- [{title}]({fname}) — {len(chunk)} edges")
                index_lines.append("")
        (out_dir / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")
        # Guided start so it doesn't feel overwhelming
        start_here = [
            "# Start here",
            "",
            "You don't have to review everything at once.",
            "",
            "**What to do:** Open [INDEX.md](INDEX.md). The list is ordered **smallest first** (fewest edges per file). Open the first file, check that each \"From\" → \"To\" link makes sense, then move to the next. Leave the big files (references, supplements) for when you're ready.",
            "",
            "**Only the small stuff?** To generate section files only for relation types with ≤10 edges (quick audit):",
            "```bash",
            "python -m propra.graph.audit_relations --sections-dir propra/data/audit_sections --max-edges-per-relation 10",
            "```",
            "",
        ]
        (out_dir / "START_HERE.md").write_text("\n".join(start_here), encoding="utf-8")
        print(f"Section audit written to {out_dir.resolve()}")
        print(f"  START_HERE.md — what to do first (read this)")
        print(f"  INDEX.md — index of all sections")
        print(f"  Open .md files in an editor to review full text.")
        if export_path is None and (sample_per_type or 0) == 0:
            return

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
    parser.add_argument(
        "--sections-dir",
        dest="sections_dir",
        nargs="?",
        const=_DEFAULT_SECTIONS_DIR,
        metavar="DIR",
        help="Write section-by-section Markdown files (full text, no truncation). Default: propra/data/audit_sections",
    )
    parser.add_argument(
        "--by-paragraph",
        action="store_true",
        help="With --sections-dir: one file per source_paragraph (e.g. §5, §6) instead of per relation type",
    )
    parser.add_argument(
        "--edges-per-file",
        type=int,
        default=_EDGES_PER_FILE,
        help=f"Max edges per Markdown file when using --sections-dir (default: {_EDGES_PER_FILE})",
    )
    parser.add_argument(
        "--max-edges-per-relation",
        type=int,
        metavar="N",
        help="With --sections-dir: only write files for relation types that have ≤ N edges (e.g. 10 = quick audit, small files only)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    args = parser.parse_args()

    run_audit(
        graph_path=args.graph,
        relation_filter=args.relation_filter or None,
        sample_per_type=args.sample,
        include_structural=args.include_structural,
        export_path=args.export_path,
        sections_dir=args.sections_dir,
        by_paragraph=args.by_paragraph,
        edges_per_file=args.edges_per_file,
        max_edges_per_relation=args.max_edges_per_relation,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

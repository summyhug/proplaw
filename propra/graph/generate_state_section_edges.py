"""
Generate a reviewable per-state section-edge module from a fine inventory + MBO mapping.

The output is meant to be a draft, modeled on Brandenburg's curated section-edge file:
- structural edges from the fine inventory (`supplements`, `sub_item_of`)
- MBO-projected domain edges where the state's mapping file has confirmed matches

Usage:
    python -m propra.graph.generate_state_section_edges --state BayBO
    python -m propra.graph.generate_state_section_edges --state NBauO --output /tmp/nbauo_section_edges.py
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from propra.graph.builder import add_node, create_graph
from propra.graph.parse_inventory import parse_inventory
from propra.graph.schema import Edge, Node
from propra.graph.state_mbo_edges import mapping_path_for_state, state_edges_from_mbo

_DATA = Path(__file__).parent.parent / "data"
_NODE_INVENTORY_DIR = "node inventory"
_GRAPH_DIR = Path(__file__).parent


def _state_config(state: str) -> dict:
    """
    Return basic config for a registered state or derive sensible defaults.
    """
    from propra.graph.build_graph import _STATE_REGISTRY  # local import to avoid startup coupling

    for cfg in _STATE_REGISTRY:
        if cfg["name"] == state:
            return cfg
    return {
        "name": state,
        "inventory": f"{state}_node_inventory_fine.md",
        "prefix": f"{state}_",
        "source_suffix": state,
        "jurisdiction": "DE-XX",
    }


def module_filename_for_state(state: str) -> str:
    """Return the default module filename for a state's draft section edges."""
    return f"{state.lower()}_section_edges.py"


def _inventory_path(cfg: dict) -> Path:
    return _DATA / _NODE_INVENTORY_DIR / cfg["inventory"]


def _mapping_path(cfg: dict) -> Path:
    return mapping_path_for_state(cfg["name"])


def _section_from_node_id(nid: str, prefix: str) -> str | None:
    """Extract § number from a state node id, e.g. BayBO_§6_1.1 -> 6."""
    if not nid.startswith(f"{prefix}§"):
        return None
    rest = nid[len(prefix) + 1 :]
    m = re.match(r"^(\d+[a-z]?)", rest)
    return m.group(1) if m else None


def _escape(s: str) -> str:
    """Escape a string for use inside generated Python source."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _edge_to_python(e: Edge) -> str:
    """Format one Edge as a Python Edge(...) call."""
    meta = ", ".join(f'"{k}": "{_escape(str(v))}"' for k, v in (e.metadata or {}).items())
    meta_str = "{" + meta + "}" if meta else "{}"
    return (
        f'    edges.append(Edge(\n'
        f'        source="{_escape(e.source)}",\n'
        f'        target="{_escape(e.target)}",\n'
        f'        relation="{_escape(e.relation)}",\n'
        f'        sourced_from="{_escape(e.sourced_from)}",\n'
        f'        metadata={meta_str},\n'
        f'    ))'
    )


def _section_title_map(path: Path) -> dict[str, str]:
    """Extract simple § number -> title mapping from a fine or paragraph inventory."""
    titles: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^###\s+§§?\s*(\d+[a-z]?)\s*[—\-]\s*(.+)", line.strip(), re.IGNORECASE)
        if not m:
            continue
        sec, title = m.group(1).lower(), m.group(2).strip()
        titles.setdefault(sec, title)
    return titles


def _slug(text: str) -> str:
    text = text.lower()
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")[:48] or "section"


def _structural_edges_from_graph(G, prefix: str) -> list[Edge]:
    """
    Build structural edges from state nodes: supplements (content -> section anchor)
    and sub_item_of (B.S -> B.1 within each paragraph block).
    """
    edges: list[Edge] = []
    law_name = prefix.rstrip("_")
    pattern = re.compile(r"§(\d+[a-z]?)_(\d+)\.(\d+)$")
    by_section: dict[str, list[tuple[str, str, int]]] = defaultdict(list)

    for nid in G.nodes():
        if not nid.startswith(prefix):
            continue
        rest = nid[len(prefix):]
        m = pattern.match(rest)
        if not m:
            continue
        section_num, block, sub = m.group(1), m.group(2), int(m.group(3))
        by_section[section_num].append((nid, block, sub))

    for section_num, node_list in by_section.items():
        section_anchor = f"{prefix}§{section_num}"
        if section_anchor not in G:
            continue
        source_para = f"§{section_num} {law_name}"

        for nid, _block, _sub in node_list:
            edges.append(
                Edge(
                    source=nid,
                    target=section_anchor,
                    relation="supplements",
                    sourced_from=source_para,
                    metadata={"reasoning": "Content node under section (structural)."},
                )
            )

        block_lead: dict[str, str] = {}
        block_members: dict[str, list[str]] = defaultdict(list)
        for nid, block, sub in node_list:
            if sub == 1:
                block_lead[block] = nid
            else:
                block_members[block].append(nid)
        for block, lead_nid in block_lead.items():
            for member_nid in block_members.get(block, []):
                edges.append(
                    Edge(
                        source=member_nid,
                        target=lead_nid,
                        relation="sub_item_of",
                        sourced_from=source_para,
                        metadata={"reasoning": "List item under same paragraph block (structural)."},
                    )
                )

    return edges


def _build_minimal_state_graph(cfg: dict):
    """Create a graph containing only this state's nodes and section anchors."""
    nodes = parse_inventory(
        path=str(_inventory_path(cfg)),
        node_prefix=cfg["prefix"],
        source_suffix=cfg["source_suffix"],
    )
    G = create_graph()
    for n in nodes:
        try:
            add_node(G, n)
        except ValueError:
            pass

    sections: set[str] = set()
    for n in nodes:
        m = re.search(r"§\s*(\d+[a-z]?)", n.source_paragraph or "")
        if m:
            sections.add(m.group(1))

    for num in sorted(sections, key=lambda s: (int(re.match(r"^(\d+)", s).group(1)), s)):
        nid = f"{cfg['prefix']}§{num}"
        if nid in G:
            continue
        add_node(
            G,
            Node(
                id=nid,
                type="allgemeine_anforderung",
                jurisdiction=cfg["jurisdiction"],
                source_paragraph=f"§{num} {cfg['source_suffix']}",
                text=f"§ {num} {cfg['source_suffix']}",
            ),
        )

    return G


def generate_for_state(state: str) -> str:
    """Build a minimal state graph and return the generated section-edge module source."""
    cfg = _state_config(state)
    prefix = cfg["prefix"]
    inv_path = _inventory_path(cfg)
    G = _build_minimal_state_graph(cfg)
    structural_edges = _structural_edges_from_graph(G, prefix)
    mbo_edges = state_edges_from_mbo(G, prefix, _mapping_path(cfg))

    struct_by_section: dict[str, list[Edge]] = defaultdict(list)
    mbo_by_section: dict[str, list[Edge]] = defaultdict(list)
    for e in structural_edges:
        sec = _section_from_node_id(e.source, prefix)
        if sec:
            struct_by_section[sec].append(e)
    for e in mbo_edges:
        sec = _section_from_node_id(e.source, prefix)
        if sec:
            mbo_by_section[sec].append(e)

    titles = _section_title_map(inv_path)
    all_sections = sorted(
        set(struct_by_section) | set(mbo_by_section),
        key=lambda s: (int(re.match(r"^(\d+)", s).group(1)), s),
    )

    lines = [
        '"""',
        f"Section-by-section edges for {cfg['full_name'] if 'full_name' in cfg else state}.",
        "",
        "Generated by generate_state_section_edges.py: structural (supplements, sub_item_of)",
        "from the fine inventory plus MBO-projected domain edges. Review and adapt.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import List",
        "",
        "from propra.graph.schema import Edge",
        "",
    ]

    def _sec_key(s: str):
        m = re.match(r"^(\d+)", s)
        return (int(m.group(1)) if m else 0, s)

    for sec in all_sections:
        title_slug = _slug(titles.get(sec.lower(), "")) if titles.get(sec.lower()) else sec.replace(".", "_")
        fn_name = f"section_{sec.replace('.', '_')}_{title_slug}"

        seen: set[tuple[str, str, str]] = set()
        merged: list[Edge] = []
        for e in struct_by_section.get(sec, []) + mbo_by_section.get(sec, []):
            key = (e.source, e.target, e.relation)
            if key in seen:
                continue
            seen.add(key)
            merged.append(e)

        lines.append("")
        lines.append(f"def {fn_name}() -> List[Edge]:")
        lines.append(
            f'    """§{sec} {cfg["source_suffix"]} — structural + MBO-projected; review and adapt."""'
        )
        lines.append("    edges: List[Edge] = []")
        for e in merged:
            lines.append(_edge_to_python(e))
        lines.append("    return edges")

    lines.append("")
    lines.append("")
    lines.append("def edges() -> List[Edge]:")
    lines.append('    """Aggregate all section-defined edges (structural + domain)."""')
    lines.append("    all_edges: List[Edge] = []")
    for sec in sorted(all_sections, key=_sec_key):
        title_slug = _slug(titles.get(sec.lower(), "")) if titles.get(sec.lower()) else sec.replace(".", "_")
        fn_name = f"section_{sec.replace('.', '_')}_{title_slug}"
        lines.append(f"    all_edges.extend({fn_name}())")
    lines.append("    return all_edges")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a reviewable state section-edge module from fine inventory + MBO mapping.")
    parser.add_argument("--state", required=True, help="State short name, e.g. BayBO or NBauO")
    parser.add_argument("--output", help="Optional output path. Defaults to propra/graph/{state_lower}_section_edges.py")
    args = parser.parse_args()

    content = generate_for_state(args.state)
    output = Path(args.output) if args.output else (_GRAPH_DIR / module_filename_for_state(args.state))
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output} (generated from MBO mapping). Review and adapt.")


if __name__ == "__main__":
    main()

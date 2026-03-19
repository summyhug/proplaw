"""
Generate `bbgbo_section_edges.py` for Brandenburg (BbgBO).

Builds a minimal graph with BbgBO nodes, generates:
- structural edges from the fine inventory (`supplements`, `sub_item_of`), and
- MBO-projected domain edges via the BbgBO↔MBO section mapping,

groups all edges by §, and writes Python code so you get a full draft
to review and adapt. Run once, then edit `bbgbo_section_edges.py` by hand.

Usage:
    python -m propra.graph.generate_bbgbo_section_edges
"""

from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict

from propra.graph.builder import create_graph, add_node
from propra.graph.parse_inventory import parse_inventory
from propra.graph.schema import Node, Edge
from propra.graph.bbgbo_mbo_edges import bbgbo_edges_from_mbo

_DATA = Path(__file__).parent.parent / "data"
_NODE_INVENTORY_DIR = "node inventory"
_MAPPING_FILE = _DATA / "BbgBO_mbo_mapping.json"
_OUTPUT_FILE = Path(__file__).parent / "bbgbo_section_edges.py"

# Section number -> short name for function (safe identifier)
_SECTION_SLUG: dict[str, str] = {
    "1": "anwendungsbereich",
    "2": "begriffe",
    "3": "allgemeine_anforderungen",
    "4": "bebauung_grundstuecke",
    "5": "zugaenge_zufahrten",
    "6": "abstandsflaechen",
    "7": "grundstuecksteilung",
    "8": "freiflaechen_kinderspielplaetze",
    "9": "gestaltung",
    "10": "aussenwerbung",
    "11": "baustelle",
    "12": "standsicherheit",
    "13": "schutz_schaedliche_einfluesse",
    "14": "brandschutz",
    "15": "waerme_schall_erschuetterung",
    "16": "verkehrssicherheit",
    "16a": "bauarten",
    "16b": "bauprodukte",
    "16c": "ce_bauprodukte",
    "17": "verwendbarkeitsnachweise",
    "18": "bauaufsichtliche_zulassung",
    "19": "pruefzeugnis",
    "20": "nachweis_verwendbarkeit",
    "21": "uebereinstimmungsbestaetigung",
    "22": "uebereinstimmungserklaerung",
    "23": "zertifizierung",
    "24": "pruefstellen",
    "25": "sachkunde_sorgfalt",
    "26": "brandverhalten",
    "27": "tragende_waende",
    "28": "aussenwaende",
    "29": "trennwaende",
    "30": "brandwaende",
    "31": "decken",
    "32": "daecher",
    "33": "rettungsweg",
    "34": "treppen",
    "35": "treppenraeume",
    "36": "flure",
    "37": "fenster_tueren",
    "38": "umwehrungen",
    "39": "aufzuege",
    "40": "leitungsanlagen",
    "41": "lueftungsanlagen",
    "42": "feuerungsanlagen",
    "43": "sanitaer",
    "44": "kleinklaeranlagen",
    "45": "abfallstoffe",
    "46": "blitzschutz",
    "47": "aufenthaltsraeume",
    "48": "wohnungen",
    "49": "stellplaetze",
    "50": "barrierefreiheit",
    "51": "sonderbauten",
}


def _section_from_source_id(nid: str) -> str | None:
    """Extract § number from BbgBO node id, e.g. BbgBO_§6_1.1 -> 6, BbgBO_§29 -> 29."""
    if not nid.startswith("BbgBO_§"):
        return None
    rest = nid[7:]  # after BbgBO_§
    m = re.match(r"^(\d+[a-z]?)", rest)
    return m.group(1) if m else None


def _escape(s: str) -> str:
    """Escape string for use inside Python source (double quotes, backslashes)."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _edge_to_python(e) -> str:
    """Format one Edge as a Python Edge(...) call (no leading comma)."""
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


def _structural_edges_from_graph(G, prefix: str) -> list[Edge]:
    """
    Build structural edges from BbgBO nodes: supplements (content → section anchor)
    and sub_item_of (B.S → B.1 within each block). Same logic as state_structural_edges.
    """
    edges: list[Edge] = []
    law_name = prefix.rstrip("_")
    # Content nodes: §N_B.S
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
        sp = f"§{section_num} {law_name}"

        # supplements: every content node → section anchor
        for nid, _block, _sub in node_list:
            edges.append(Edge(
                source=nid,
                target=section_anchor,
                relation="supplements",
                sourced_from=sp,
                metadata={"reasoning": "Content node under section (structural)."},
            ))

        # sub_item_of: B.S → B.1 within each block
        block_lead: dict[str, str] = {}
        block_members: dict[str, list[str]] = defaultdict(list)
        for nid, block, sub in node_list:
            if sub == 1:
                block_lead[block] = nid
            else:
                block_members[block].append(nid)
        for block, lead_nid in block_lead.items():
            for member_nid in block_members.get(block, []):
                edges.append(Edge(
                    source=member_nid,
                    target=lead_nid,
                    relation="sub_item_of",
                    sourced_from=sp,
                    metadata={"reasoning": "List item under same paragraph block (structural)."},
                ))

    return edges


def _build_minimal_bbgbo_graph():
    """Create a graph containing only BbgBO nodes and section anchors."""
    inv_path = str(_DATA / _NODE_INVENTORY_DIR / "BbgBO_node_inventory_fine.md")
    nodes = parse_inventory(
        path=inv_path,
        node_prefix="BbgBO_",
        source_suffix="BbgBO",
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
    for num in sorted(sections, key=lambda x: (x.rstrip("a"), x)):
        nid = f"BbgBO_§{num}"
        if nid in G:
            continue
        add_node(G, Node(
            id=nid,
            type="allgemeine_anforderung",
            jurisdiction="DE-BB",
            source_paragraph=f"§{num} BbgBO",
            text=f"§ {num} BbgBO",
        ))
    return G


def generate() -> str:
    """Build minimal graph, get structural + MBO-projected edges by §, return full file content."""
    G = _build_minimal_bbgbo_graph()
    mbo_edges = bbgbo_edges_from_mbo(G, "BbgBO_", _MAPPING_FILE)
    structural_edges = _structural_edges_from_graph(G, "BbgBO_")

    # Group MBO and structural by section
    mbo_by_section: dict[str, list[Edge]] = defaultdict(list)
    struct_by_section: dict[str, list[Edge]] = defaultdict(list)
    for e in mbo_edges:
        sec = _section_from_source_id(e.source)
        if sec:
            mbo_by_section[sec].append(e)
    for e in structural_edges:
        sec = _section_from_source_id(e.source)
        if sec:
            struct_by_section[sec].append(e)

    # All section numbers that have any edges
    all_sections = sorted(
        set(mbo_by_section.keys()) | set(struct_by_section.keys()),
        key=lambda s: (int(re.match(r"^(\d+)", s).group(1)) if re.match(r"^(\d+)", s) else 0, s),
    )

    lines = [
        '"""',
        "Section-by-section edges for the Brandenburg building code (BbgBO).",
        "",
        "Generated by generate_bbgbo_section_edges.py: structural (supplements, sub_item_of)",
        "from the fine inventory plus MBO-projected domain edges. Review and adapt.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import List",
        "",
        "from propra.graph.schema import Edge",
        "",
        "_PREFIX = \"BbgBO_\"",
        "",
        "",
        "def _n(para: str, row: str) -> str:",
        "    \"\"\"Node ID for BbgBO § para, row (e.g. §6, 2.1 → BbgBO_§6_2.1).\"\"\"",
        "    return f\"{_PREFIX}§{para}_{row}\"",
        "",
        "",
        "def _section_node(para: str) -> str:",
        "    \"\"\"Section anchor node id (e.g. §6 → BbgBO_§6).\"\"\"",
        "    return f\"{_PREFIX}§{para}\"",
        "",
    ]

    def _sec_key(s: str):
        m = re.match(r"^(\d+)", s)
        return (int(m.group(1)) if m else 0, s)

    for sec in sorted(all_sections, key=_sec_key):
        slug = _SECTION_SLUG.get(sec, sec)
        fn_name = f"section_{sec}_{slug}"
        # Merge: structural first, then MBO; dedupe by (source, target, relation)
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
        lines.append(f'    """§{sec} BbgBO — structural + MBO-projected; review and adapt."""')
        lines.append("    edges: List[Edge] = []")
        for e in merged:
            lines.append(_edge_to_python(e))
        lines.append("    return edges")

    # edges() aggregator
    lines.append("")
    lines.append("")
    lines.append("def edges() -> List[Edge]:")
    lines.append("    \"\"\"Aggregate all BbgBO section-defined edges (structural + domain).\"\"\"")
    lines.append("    all_edges: List[Edge] = []")
    for sec in sorted(all_sections, key=_sec_key):
        slug = _SECTION_SLUG.get(sec, sec)
        fn_name = f"section_{sec}_{slug}"
        lines.append(f"    all_edges.extend({fn_name}())")
    lines.append("    return all_edges")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    content = generate()
    _OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Wrote {_OUTPUT_FILE} (generated from MBO mapping). Review and adapt.")


if __name__ == "__main__":
    main()

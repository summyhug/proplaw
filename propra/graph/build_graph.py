"""
Build the Propra core knowledge graph (MBO + all registered state LBOs).

Loads nodes from MBO_node_inventory.md and each entry in _STATE_REGISTRY,
adds structural edges + section-defined edges + reference edges.
Saves to graph.pkl and graph.graphml. This graph is the single source of truth.

To add a new state: drop its *_node_inventory.md into propra/data/node inventory/ and append
one entry to _STATE_REGISTRY — no other code changes required.

Usage:
    python -m propra.graph.build_graph
"""

import argparse
import re
from collections import defaultdict
from pathlib import Path

import networkx as nx

from propra.graph.builder import add_edge, add_node, create_graph, graph_summary, save_graph
from propra.graph.parse_inventory import parse_inventory
from propra.graph.schema import Node
from propra.graph.visualize import export_graphml
from propra.graph.mbo_section_edges import edges as mbo_section_edges
from propra.graph.references_edges import references_edges
from propra.graph.state_structural_edges import state_structural_edges
from propra.graph.bbgbo_mbo_edges import bbgbo_edges_from_mbo

_DATA = Path(__file__).parent.parent / "data"
_NODE_INVENTORY_DIR = "node inventory"

_MBO_INVENTORY = str(_DATA / _NODE_INVENTORY_DIR / "MBO_node_inventory.md")
_GRAPH_PATH = str(_DATA / "graph.pkl")
_GRAPHML_PATH = str(_DATA / "graph.graphml")

# Registry of state LBOs to include in the graph.
# To add a new state: append one entry here and drop the inventory file in propra/data/node inventory/.
_STATE_REGISTRY = [
    {
        "name": "BbgBO",
        "full_name": "Brandenburgische Bauordnung (BbgBO)",
        "inventory": "BbgBO_node_inventory_fine.md",
        "prefix": "BbgBO_",
        "source_suffix": "BbgBO",
        "jurisdiction": "DE-BB",
    },
]

# Sections to include (add § numbers as we go)
_SECTIONS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "11", "12", "13", "14", "15", "16", "16a", "16b", "16c",
    "17", "18", "19", "20", "21", "22", "23", "24",
    "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37", "38",
    "39", "40", "41", "42", "43", "44", "45", "46",
    "47", "48", "49", "50", "51",
    "52", "53", "54", "55", "56", "57", "58", "59", "60",
    "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72",
    "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86",
]

# Section number -> (title, type for section anchor node)
_SECTION_ANCHORS = {
    "1": ("Anwendungsbereich", "anwendungsbereich"),
    "2": ("Begriffe", "begriffsbestimmung"),
    "3": ("Allgemeine Anforderungen", "allgemeine_anforderung"),
    "4": ("Bebauung der Grundstücke mit Gebäuden", "grundstuecksbebauung"),
    "5": ("Zugänge und Zufahrten auf den Grundstücken", "grundstuecksbebauung"),
    "6": ("Abstandsflächen, Abstände", "abstandsflaeche"),
    "7": ("Teilung von Grundstücken", "grundstuecksteilung"),
    "8": ("Nicht überbaute Flächen, Kinderspielplätze", "freiflaechengestaltung"),
    "9": ("Gestaltung", "gestaltungsanforderung"),
    "10": ("Anlagen der Außenwerbung, Warenautomaten", "gestaltungsanforderung"),
    "11": ("Baustelle", "baustellenanforderung"),
    "12": ("Standsicherheit", "standsicherheit"),
    "13": ("Schutz gegen schädliche Einflüsse", "allgemeine_anforderung"),
    "14": ("Brandschutz", "brandschutzanforderung"),
    "15": ("Wärme-, Schall-, Erschütterungsschutz", "allgemeine_anforderung"),
    "16": ("Verkehrssicherheit", "verkehrssicherheit"),
    "16a": ("Bauarten", "allgemeine_anforderung"),
    "16b": ("Bauprodukte (allg. Anforderungen)", "allgemeine_anforderung"),
    "16c": ("CE-gekennzeichnete Bauprodukte", "allgemeine_anforderung"),
    "17": ("Verwendbarkeitsnachweise", "allgemeine_anforderung"),
    "18": ("Allgemeine bauaufsichtliche Zulassung", "genehmigungspflicht"),
    "19": ("Allgemeines bauaufsichtliches Prüfzeugnis", "genehmigungspflicht"),
    "20": ("Nachweis Verwendbarkeit im Einzelfall", "allgemeine_anforderung"),
    "21": ("Übereinstimmungsbestätigung", "allgemeine_anforderung"),
    "22": ("Übereinstimmungserklärung des Herstellers", "allgemeine_anforderung"),
    "23": ("Zertifizierung", "allgemeine_anforderung"),
    "24": ("Prüf-, Zertifizierungs-, Überwachungsstellen", "allgemeine_anforderung"),
    "25": ("Sachkunde- und Sorgfaltsanforderungen", "allgemeine_anforderung"),
    "26": ("Brandverhalten von Baustoffen und Bauteilen", "brandklassifizierung"),
    "27": ("Tragende Wände, Stützen", "tragende_wand"),
    "28": ("Außenwände", "aussenwand"),
    "29": ("Trennwände", "trennwand"),
    "30": ("Brandwände", "brandwand"),
    "31": ("Decken", "decke"),
    "32": ("Dächer", "dach"),
    "33": ("Erster und zweiter Rettungsweg", "treppe"),
    "34": ("Treppen", "treppe"),
    "35": ("Notwendige Treppenräume, Ausgänge", "treppenraum"),
    "36": ("Notwendige Flure, offene Gänge", "notwendiger_flur"),
    "37": ("Fenster, Türen, sonstige Öffnungen", "fensteroffnung"),
    "38": ("Umwehrungen", "schutzanforderung"),
    "39": ("Aufzüge", "aufzugsanlage"),
    "40": ("Leitungsanlagen, Installationsschächte und -kanäle", "technische_anlage"),
    "41": ("Lüftungsanlagen", "technische_anlage"),
    "42": ("Feuerungsanlagen, sonstige Anlagen zur Wärmeerzeugung", "technische_anlage"),
    "43": ("Sanitäre Anlagen, Wasserzähler", "sanitaerraum"),
    "44": ("Kleinkläranlagen, Gruben", "technische_anlage"),
    "45": ("Aufbewahrung fester Abfallstoffe", "gemeinschaftsanlage"),
    "46": ("Blitzschutzanlagen", "technische_anlage"),
    "47": ("Aufenthaltsräume", "aufenthaltsraum"),
    "48": ("Wohnungen", "wohnung"),
    "49": ("Stellplätze, Garagen und Abstellplätze für Fahrräder", "stellplatzpflicht"),
    "50": ("Barrierefreies Bauen", "barrierefreiheit"),
    "51": ("Sonderbauten", "sonderbautyp"),
    # Procedure, authorities, approval (§52–§86) — for "what's needed" (who, what to submit, when)
    "52": ("Grundpflichten", "beteiligtenpflicht"),
    "53": ("Bauherr", "beteiligtenpflicht"),
    "54": ("Entwurfsverfasser", "beteiligtenpflicht"),
    "55": ("Unternehmer", "beteiligtenpflicht"),
    "56": ("Bauleiter", "beteiligtenpflicht"),
    "57": ("Aufbau und Zuständigkeit der Bauaufsichtsbehörden", "behoerdenstruktur"),
    "58": ("Aufgaben und Befugnisse der Bauaufsichtsbehörden", "behoerdenstruktur"),
    "59": ("Grundsatz", "genehmigungspflicht"),
    "60": ("Vorrang anderer Gestattungsverfahren", "genehmigungspflicht"),
    "61": ("Verfahrensfreie Bauvorhaben, Beseitigung von Anlagen", "verfahrensfreiheit"),
    "62": ("Genehmigungsfreistellung", "genehmigungspflicht"),
    "63": ("Vereinfachtes Baugenehmigungsverfahren", "vereinfachtes_genehmigungsverfahren"),
    "64": ("Baugenehmigungsverfahren", "genehmigungspflicht"),
    "65": ("Bauvorlageberechtigung", "bauantrag"),
    "66": ("Bautechnische Nachweise", "genehmigungspflicht"),
    "67": ("Abweichungen", "abweichung"),
    "68": ("Bauantrag, Bauvorlagen", "bauantrag"),
    "69": ("Behandlung des Bauantrags", "bauantrag"),
    "70": ("Beteiligung der Nachbarn und der Öffentlichkeit", "nachbarbenachrichtigung"),
    "71": ("Ersetzung des gemeindlichen Einvernehmens", "genehmigungspflicht"),
    "72": ("Baugenehmigung, Baubeginn", "baugenehmigung"),
    "73": ("Geltungsdauer der Genehmigung", "verfahrensfrist"),
    "74": ("Teilbaugenehmigung", "baugenehmigung"),
    "75": ("Vorbescheid", "bauvorbescheid"),
    "76": ("Fliegende Bauten", "typengenehmigung"),
    "77": ("Bauaufsichtliche Zustimmung", "genehmigungspflicht"),
    "78": ("Verbot unrechtmäßig gekennzeichneter Bauprodukte", "genehmigungspflicht"),
    "79": ("Einstellung von Arbeiten", "behoerdenstruktur"),
    "80": ("Beseitigung von Anlagen, Nutzungsuntersagung", "behoerdenstruktur"),
    "81": ("Bauüberwachung", "bauueberwachung"),
    "82": ("Bauzustandsanzeigen, Aufnahme der Nutzung", "genehmigungspflicht"),
    "83": ("Baulasten, Baulastenverzeichnis", "genehmigungspflicht"),
    "84": ("Ordnungswidrigkeiten", "sanktion"),
    "85": ("Rechtsvorschriften", "schlussvorschrift"),
    "86": ("Örtliche Bauvorschriften", "oertliche_bauvorschrift"),
}


def _para_number_from_source(source_paragraph: str) -> str | None:
    """Extract § number from source_paragraph, e.g. '§1 Abs. 2 MBO' -> '1'."""
    if not source_paragraph:
        return None
    m = re.search(r"§\s*(\d+[a-z]?)", source_paragraph.strip(), re.IGNORECASE)
    return m.group(1).lower() if m else None


def _add_structural_edges(G: nx.DiGraph) -> int:
    """Add 'supplements' edges so every node in each section connects to its anchor."""
    groups = defaultdict(list)
    for nid, data in G.nodes(data=True):
        src_para = data.get("source_paragraph", "")
        group = data.get("group", "")
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
                structural=True,
            )
            added += 1
    return added


def _load_mbo_nodes() -> list:
    """Parse MBO inventory and return nodes for included sections only."""
    nodes = parse_inventory(path=_MBO_INVENTORY)
    filtered = [n for n in nodes if _para_number_from_source(n.source_paragraph) in _SECTIONS]
    return filtered


def _load_state_nodes(config: dict) -> list:
    """Parse a state LBO inventory; all sections included (independent of MBO)."""
    path = str(_DATA / _NODE_INVENTORY_DIR / config["inventory"])
    return parse_inventory(
        path=path,
        node_prefix=config["prefix"],
        source_suffix=config["source_suffix"],
    )


def _section_numbers(nodes: list) -> set[str]:
    """Unique § numbers extracted from nodes' source_paragraph."""
    return {_para_number_from_source(n.source_paragraph) for n in nodes
            if _para_number_from_source(n.source_paragraph)}


def _add_law_root(G: nx.DiGraph, prefix: str, text: str, jurisdiction: str, source_suffix: str) -> int:
    """
    Create a root node for a law and connect all its section anchors to it via supplements.

    The root node ID is {prefix}ROOT (e.g. MBO_ROOT, BbgBO_ROOT).
    Section anchors are identified as nodes whose ID matches {prefix}§N exactly
    (no trailing underscore — they are anchors, not content nodes).

    Returns the number of supplements edges added.
    """
    root_id = f"{prefix}ROOT"
    add_node(G, Node(
        id=root_id,
        type="gesetz",
        jurisdiction=jurisdiction,
        source_paragraph=source_suffix,
        text=text,
    ))

    added = 0
    for nid in G.nodes():
        if nid == root_id:
            continue
        if not nid.startswith(prefix):
            continue
        # Section anchors: {prefix}§N with no further underscore-delimited parts
        rest = nid[len(prefix):]
        if re.match(r"^§\d+[a-z]?$", rest) and not G.has_edge(nid, root_id):
            G.add_edge(nid, root_id, relation="supplements", sourced_from=source_suffix, structural=True)
            added += 1
    return added


def _apply_edges(G: nx.DiGraph, edge_list: list, label: str) -> None:
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
    """Build the core graph and save to graph.pkl / graph.graphml."""
    print("=== Propra — Core graph build ===\n")
    print(f"Sections: §{', §'.join(_SECTIONS)}\n")

    G = create_graph()
    G.graph["name"] = "Propra Wissensgraph"
    G.graph["jurisdiction"] = "DE-MBO"
    G.graph["source"] = "Musterbauordnung (MBO) + Landesbauordnungen"

    failed_nodes = 0

    # 1. Load nodes
    print("Loading nodes:")

    # MBO
    mbo_nodes = _load_mbo_nodes()
    print(f"  MBO: {len(mbo_nodes)} nodes")
    for node in mbo_nodes:
        try:
            add_node(G, node)
        except ValueError as e:
            print(f"    [ERROR] {node.id}: {e}")
            failed_nodes += 1

    # MBO section anchors
    for num in _SECTIONS:
        nid = f"MBO_§{num}"
        if nid in G:
            continue
        title, stype = _SECTION_ANCHORS.get(num, (f"§{num}", "allgemeine_anforderung"))
        add_node(G, Node(
            id=nid,
            type=stype,
            jurisdiction="DE-MBO",
            source_paragraph=f"§{num} MBO",
            text=title,
        ))
    print(f"  MBO section anchors: {len(_SECTIONS)}")

    # State LBOs (registry-driven)
    state_nodes_by_prefix: dict[str, list] = {}
    for cfg in _STATE_REGISTRY:
        nodes = _load_state_nodes(cfg)
        print(f"  {cfg['name']}: {len(nodes)} nodes")
        for node in nodes:
            try:
                add_node(G, node)
            except ValueError as e:
                print(f"    [ERROR] {node.id}: {e}")
                failed_nodes += 1

        # Section anchor nodes — one per § in the state inventory
        sections = sorted(_section_numbers(nodes))
        for num in sections:
            nid = f"{cfg['prefix']}§{num}"
            if nid in G:
                continue
            # Reuse MBO type where § numbering matches; fall back to allgemeine_anforderung
            _, stype = _SECTION_ANCHORS.get(num, (None, "allgemeine_anforderung"))
            add_node(G, Node(
                id=nid,
                type=stype,
                jurisdiction=cfg["jurisdiction"],
                source_paragraph=f"§{num} {cfg['source_suffix']}",
                text=f"§ {num} {cfg['source_suffix']}",
            ))
        print(f"  {cfg['name']} section anchors: {len(sections)}")
        state_nodes_by_prefix[cfg["prefix"]] = nodes

    # 2. Law root nodes — one per law, all section anchors connect to it
    mbo_root_edges = _add_law_root(G, "MBO_", "Musterbauordnung (MBO)", "DE-MBO", "MBO")
    print("\nLaw root nodes:")
    print(f"  MBO_ROOT: {mbo_root_edges} section anchors connected")
    for cfg in _STATE_REGISTRY:
        n = _add_law_root(G, cfg["prefix"], cfg["full_name"], cfg["jurisdiction"], cfg["source_suffix"])
        print(f"  {cfg['prefix']}ROOT: {n} section anchors connected")

    # 3. Structural edges (supplements: content nodes → section anchors)
    structural = _add_structural_edges(G)
    print(f"\nStructural edges: {structural} supplements added")

    # 3. Domain edges
    print("\nDomain edges:")
    _apply_edges(G, mbo_section_edges(), "MBO section (§1 exclusions)")
    for cfg in _STATE_REGISTRY:
        edges = state_structural_edges(G, cfg["prefix"])
        _apply_edges(G, edges, f"{cfg['name']} structural (sub_item_of)")
        # Copy MBO relationship structure onto this state where section mapping exists
        mapping_path = _DATA / f"{cfg['name']}_mbo_mapping.json"
        if mapping_path.exists():
            mbo_copied = bbgbo_edges_from_mbo(G, cfg["prefix"], mapping_path)
            _apply_edges(G, mbo_copied, f"{cfg['name']} from MBO (mapping)")
    ref_edges = references_edges(G)
    _apply_edges(G, ref_edges, "references (from text)")

    # 4. Summary
    summary = graph_summary(G)
    orphans = sum(1 for n in G.nodes if G.degree(n) == 0)
    print(f"\n{'─' * 45}")
    print(f"Nodes     : {summary['node_count']}  (failed: {failed_nodes})")
    print(f"Edges     : {summary['edge_count']}")
    print(f"Orphans   : {orphans}")
    print("\nRelation types:")
    for r, count in sorted(summary["relation_types"].items(), key=lambda x: -x[1]):
        print(f"  {r:<30} {count}")

    save_graph(G, _GRAPH_PATH)
    export_graphml(G, _GRAPHML_PATH)
    print(f"\nSaved: {_GRAPH_PATH}")
    return G


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Propra core knowledge graph (MBO, section by section).")
    args = parser.parse_args()
    build()

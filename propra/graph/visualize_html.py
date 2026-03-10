"""
Interactive HTML visualisation for the Propra knowledge graph using pyvis.

Generates a self-contained HTML file you open in any browser.
Nodes are colour-coded by type, sized by connectivity, and show full
legal text + source citation on hover/click.

Usage — full graph:
    python -m propra.graph.visualize_html

Usage — focused subgraph (e.g. just fence nodes):
    python -m propra.graph.visualize_html --filter §5 §6 A1-07 §74

Usage from Python:
    from propra.graph.visualize_html import render
    render(G, "propra/data/graph_fence.html", filter_prefixes=["§6", "A1-07"])
"""

import sys
from pathlib import Path
from typing import Optional

import networkx as nx
from pyvis.network import Network

from propra.graph.builder import load_graph

_DEFAULT_GRAPH = str(Path(__file__).parent.parent / "data" / "graph.pkl")

# ---------------------------------------------------------------------------
# Colour palette — one colour per node type group
# ---------------------------------------------------------------------------
_TYPE_COLOURS = {
    # Setback rules
    "abstandsflaeche":               "#1A3355",   # navy
    "abstandsflaeche_sonderfall":    "#2E5B8A",   # mid-blue
    "abstandsflaechenübertragung":   "#4A7FBA",   # light-blue

    # Procedure
    "verfahrensfreies_vorhaben":     "#C9952A",   # amber
    "verfahrensfreiheit":            "#E0B050",   # light-amber
    "kenntnisgabeverfahren":         "#D4A030",
    "vereinfachtes_genehmigungsverfahren": "#C08020",
    "genehmigungspflicht":           "#A06010",
    "baugenehmigung":                "#805000",

    # Numeric thresholds
    "zahlenwert":                    "#6DBF6D",   # green

    # Local / design
    "oertliche_bauvorschrift":       "#E05050",   # red
    "gestaltungsanforderung":        "#E07070",

    # Definitions / scope
    "begriffsbestimmung":            "#9B59B6",   # purple
    "anwendungsbereich":             "#7D3C98",

    # Fire / structure
    "brandschutzanforderung":        "#E74C3C",
    "brandwand":                     "#C0392B",
    "brandklassifizierung":          "#FF7675",
    "tragende_wand":                 "#D35400",
    "aussenwand":                    "#E67E22",
    "trennwand":                     "#F39C12",
    "decke":                         "#F1C40F",
    "dach":                          "#F9E79F",
}
_DEFAULT_COLOUR = "#95A5A6"   # grey for anything not listed


def _node_colour(node_type: str) -> str:
    return _TYPE_COLOURS.get(node_type, _DEFAULT_COLOUR)


def _node_tooltip(nid: str, data: dict) -> str:
    text = data.get("text", "").replace('"', "'")
    src  = data.get("source_paragraph", "")
    ntype = data.get("type", "")
    val  = data.get("numeric_value", "")
    unit = data.get("unit", "")
    ctx  = data.get("context", "")

    lines = [
        f"<b>{nid}</b>",
        f"<i>{ntype}</i>",
        f"<hr/>",
        f"{text}",
    ]
    if ctx:
        lines.append(f"<br/><small>Context: {ctx}</small>")
    if val not in (None, ""):
        lines.append(f"<br/><b>Value:</b> {val} {unit}")
    lines.append(f"<br/><small>Source: {src}</small>")
    return "".join(lines)


def _short_label(nid: str, data: dict) -> str:
    """Short label shown on the node itself — paragraph + row, strip inventory prefix."""
    label = nid.replace("BW_LBO_", "").replace("MBO_", "MBO:")
    # Truncate long annex IDs
    if len(label) > 20:
        label = label[:18] + "…"
    return label


def render(
    G: nx.DiGraph,
    output_path: str,
    filter_prefixes: Optional[list[str]] = None,
    height: str = "900px",
) -> str:
    """
    Render the graph (or a filtered subgraph) as an interactive HTML file.

    Args:
        G:               The graph to render.
        output_path:     Where to write the HTML file.
        filter_prefixes: If given, only include nodes whose ID starts with
                         'BW_LBO_' or 'MBO_' + any of these prefixes (e.g. §5, §6, A1-07).
                         Neighbours of matching nodes are included so context is never missing.
        height:          Height of the canvas in the HTML file.

    Returns:
        Absolute path to the generated HTML file.
    """
    # --- build subgraph ---
    if filter_prefixes:
        def _matches_prefix(nid: str) -> bool:
            return any(
                nid.startswith(f"BW_LBO_{p}") or nid.startswith(f"MBO_{p}")
                for p in filter_prefixes
            )
        seed_nodes = {nid for nid in G.nodes if _matches_prefix(nid)}
        # include immediate neighbours so edges don't dangle
        neighbour_nodes = set()
        for nid in seed_nodes:
            neighbour_nodes.update(G.predecessors(nid))
            neighbour_nodes.update(G.successors(nid))
        keep = seed_nodes | neighbour_nodes
        sub = G.subgraph(keep)
    else:
        sub = G

    # --- pyvis network ---
    net = Network(
        height=height,
        width="100%",
        directed=True,
        bgcolor="#F8F9FA",
        font_color="#1A3355",
        notebook=False,
    )
    net.set_options("""
    {
      "nodes": {
        "font": { "size": 12, "face": "DM Sans, sans-serif" },
        "borderWidth": 2,
        "borderWidthSelected": 4
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.7 } },
        "font": { "size": 10, "align": "middle" },
        "smooth": { "type": "dynamic" },
        "color": { "inherit": false, "color": "#888888" }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.003,
          "springLength": 120
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 150 }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    # degree map for sizing
    degrees = dict(sub.degree())
    max_deg = max(degrees.values(), default=1)

    for nid, data in sub.nodes(data=True):
        node_type = data.get("type", "")
        deg = degrees.get(nid, 0)
        size = 12 + int(30 * (deg / max(max_deg, 1)))

        net.add_node(
            nid,
            label=_short_label(nid, data),
            title=_node_tooltip(nid, data),
            color=_node_colour(node_type),
            size=size,
            shape="dot",
        )

    for src, tgt, edata in sub.edges(data=True):
        relation = edata.get("relation", "")
        # De-emphasise structural supplements (section→anchor) so domain edges stand out
        is_structural = relation == "supplements" and edata.get("structural") is True
        net.add_edge(
            src, tgt,
            label=relation,
            title=f"{relation}<br/>sourced from: {edata.get('sourced_from', '')}",
            color="#CCCCCC" if is_structural else "#1A3355",
            width=1 if is_structural else 2.5,
            dashes=is_structural,
        )

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(dest))
    print(f"HTML graph saved → {dest.resolve()}")
    print(f"Open in browser: open '{dest.resolve()}'")
    return str(dest.resolve())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    # Parse --filter flag
    filter_prefixes = None
    if "--filter" in args:
        idx = args.index("--filter")
        filter_prefixes = args[idx + 1:]
        args = args[:idx]

    graph_path = args[0] if args else _DEFAULT_GRAPH
    graph_name = Path(graph_path).stem

    suffix = "_" + "_".join(filter_prefixes) if filter_prefixes else ""
    out = str(Path(graph_path).parent / f"{graph_name}{suffix}.html")

    G = load_graph(graph_path)
    render(G, out, filter_prefixes=filter_prefixes)

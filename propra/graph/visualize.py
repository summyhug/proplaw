"""
Visualisation utilities for the Propra knowledge graph.

Two outputs:
  1. GraphML export  — open in Gephi for full interactive exploration
  2. matplotlib plot — quick node-type distribution bar chart for sanity checks

Usage:
    from propra.graph.visualize import export_graphml, plot_type_distribution
"""

from pathlib import Path
from typing import Optional

import networkx as nx


def export_graphml(G: nx.DiGraph, path: str) -> None:
    """
    Export the graph to GraphML format.

    GraphML can be opened in Gephi (free) for full interactive visualisation
    with layout algorithms, filtering, and relation inspection.

    Args:
        G:    The graph to export.
        path: Output file path (e.g. 'propra/data/graph_base.graphml').
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Work on a shallow copy so we don't mutate the live graph
    G = G.copy()

    # Gephi does not support graph-level attributes in GraphML — remove them
    # to suppress import warnings. The same info lives on every node already.
    for key in ("name", "jurisdiction", "source"):
        G.graph.pop(key, None)

    # NetworkX GraphML writer requires all attribute values to be serialisable;
    # replace None values with empty string to avoid write errors.
    for _, data in G.nodes(data=True):
        for k, v in list(data.items()):
            if v is None:
                data[k] = ""

    nx.write_graphml(G, str(dest))
    print(f"GraphML saved: {dest}")


def plot_type_distribution(G: nx.DiGraph, save_path: Optional[str] = None) -> None:
    """
    Plot a bar chart of node counts per type.

    Requires matplotlib. If not available (e.g. NumPy compatibility issues),
    prints the distribution as text instead.

    Args:
        G:         The graph to inspect.
        save_path: If provided, save the figure to this path instead of showing it.
    """
    type_counts: dict[str, int] = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    if not type_counts:
        print("No nodes to plot.")
        return

    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"[INFO] matplotlib unavailable ({e}). Printing distribution instead:")
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {t:<40} {c}")
        return

    labels, counts = zip(*sorted(type_counts.items(), key=lambda x: -x[1]))

    fig, ax = plt.subplots(figsize=(12, max(6, len(labels) * 0.35)))
    bars = ax.barh(labels, counts, color="#1A3355")
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel("Node count")
    ax.set_title("Propra Knowledge Graph — Nodes per type", pad=12)
    ax.invert_yaxis()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Plot saved: {save_path}")
    else:
        plt.show()



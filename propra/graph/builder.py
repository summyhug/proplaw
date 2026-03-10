"""
Core functions for building, validating, and persisting the Propra knowledge graph.

All domain-specific build scripts (build_fence.py, build_garden.py, etc.)
import these functions and operate on the same graph object.

Usage:
    from propra.graph.builder import create_graph, add_node, add_edge, save_graph, load_graph

    G = create_graph()
    add_node(G, Node(...))
    add_edge(G, Edge(...))
    save_graph(G, "propra/data/graph.pkl")
"""

import pickle
from pathlib import Path

import networkx as nx

from propra.graph.schema import Edge, Node


def create_graph() -> nx.DiGraph:
    """Creates a new empty directed graph for Propra."""
    G = nx.DiGraph()
    G.graph["name"] = "Propra Wissensgraph"
    G.graph["jurisdiction"] = "DE-BW"
    G.graph["source"] = "Landesbauordnung Baden-Württemberg, Fassung ab 28. Februar 2026"
    return G


def add_node(G: nx.DiGraph, node: Node) -> None:
    """
    Validates a node and adds it to the graph.

    Args:
        G:    The target graph.
        node: Instance of Node (from schema.py).

    Raises:
        ValueError: If required fields are missing or the node type is unknown.
    """
    node.validate()
    G.add_node(
        node.id,
        type=node.type,
        jurisdiction=node.jurisdiction,
        source_paragraph=node.source_paragraph,
        text=node.text,
        numeric_value=node.numeric_value,
        unit=node.unit,
        **node.metadata,
    )


def add_edge(G: nx.DiGraph, edge: Edge) -> None:
    """
    Validates an edge and adds it to the graph.

    Args:
        G:    The target graph.
        edge: Instance of Edge (from schema.py).

    Raises:
        ValueError: If required fields are missing, the relation type is unknown,
                    or the source/target nodes do not exist in the graph.
    """
    edge.validate()
    if edge.source not in G:
        raise ValueError(f"Source node '{edge.source}' does not exist in the graph.")
    if edge.target not in G:
        raise ValueError(f"Target node '{edge.target}' does not exist in the graph.")
    G.add_edge(
        edge.source,
        edge.target,
        relation=edge.relation,
        sourced_from=edge.sourced_from,
        **edge.metadata,
    )


def save_graph(G: nx.DiGraph, path: str) -> None:
    """
    Saves the graph to a pickle file.

    Args:
        G:    The graph to save.
        path: Output file path (e.g. "propra/data/graph.pkl").
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        pickle.dump(G, f)
    print(f"Graph saved: {dest} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")


def load_graph(path: str) -> nx.DiGraph:
    """
    Loads a saved graph from a pickle file.

    Args:
        path: File path of the saved graph.

    Returns:
        nx.DiGraph: The loaded graph.

    Raises:
        FileNotFoundError: If the file is not found.
    """
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(
            f"Graph file not found: {src}. "
            "Please run a build script first."
        )
    with open(src, "rb") as f:
        G = pickle.load(f)
    print(f"Graph loaded: {src} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
    return G


def graph_summary(G: nx.DiGraph) -> dict:
    """
    Returns a summary of the graph — useful for tests and debugging.

    Returns:
        dict with node count, edge count, node types, and relation types.
    """
    node_types: dict[str, int] = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1

    relation_types: dict[str, int] = {}
    for _, _, data in G.edges(data=True):
        r = data.get("relation", "unknown")
        relation_types[r] = relation_types.get(r, 0) + 1

    return {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "node_types": node_types,
        "relation_types": relation_types,
        "source": G.graph.get("source", "unknown"),
        "jurisdiction": G.graph.get("jurisdiction", "unknown"),
    }

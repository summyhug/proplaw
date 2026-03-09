"""
Kernfunktionen zum Aufbau, zur Validierung und zur Speicherung des Propra-Wissensgraphen.

Alle domänenspezifischen Build-Skripte (build_fence.py, build_garden.py usw.)
importieren diese Funktionen und arbeiten auf demselben Graphobjekt.

Verwendung:
    from propra.graph.builder import graph_erstellen, knoten_hinzufuegen, \
                                     kante_hinzufuegen, graph_speichern, graph_laden

    G = graph_erstellen()
    knoten_hinzufuegen(G, Knoten(...))
    kante_hinzufuegen(G, Kante(...))
    graph_speichern(G, "propra/data/graph.pkl")
"""

import pickle
from pathlib import Path

import networkx as nx

from propra.graph.schema import Kante, Knoten


def graph_erstellen() -> nx.DiGraph:
    """Erstellt einen neuen, leeren gerichteten Graphen für Propra."""
    G = nx.DiGraph()
    G.graph["name"] = "Propra Wissensgraph"
    G.graph["jurisdiction"] = "DE-BW"
    G.graph["quelle"] = "Landesbauordnung Baden-Württemberg, Fassung ab 28. Februar 2026"
    return G


def knoten_hinzufuegen(G: nx.DiGraph, knoten: Knoten) -> None:
    """
    Validiert einen Knoten und fügt ihn dem Graphen hinzu.

    Args:
        G:      Der Zielgraph.
        knoten: Instanz von Knoten (aus schema.py).

    Raises:
        ValueError: Wenn Pflichtfelder fehlen oder der Knotentyp unbekannt ist.
    """
    knoten.validieren()
    G.add_node(
        knoten.id,
        type=knoten.type,
        jurisdiction=knoten.jurisdiction,
        source_paragraph=knoten.source_paragraph,
        text=knoten.text,
        zahlenwert=knoten.zahlenwert,
        einheit=knoten.einheit,
        **knoten.metadaten,
    )


def kante_hinzufuegen(G: nx.DiGraph, kante: Kante) -> None:
    """
    Validiert eine Kante und fügt sie dem Graphen hinzu.

    Args:
        G:     Der Zielgraph.
        kante: Instanz von Kante (aus schema.py).

    Raises:
        ValueError: Wenn Pflichtfelder fehlen, der Kantentyp unbekannt ist
                    oder Quell-/Zielknoten nicht im Graphen existieren.
    """
    kante.validieren()
    if kante.von not in G:
        raise ValueError(f"Quellknoten '{kante.von}' existiert nicht im Graphen.")
    if kante.nach not in G:
        raise ValueError(f"Zielknoten '{kante.nach}' existiert nicht im Graphen.")
    G.add_edge(
        kante.von,
        kante.nach,
        relation=kante.relation,
        sourced_from=kante.sourced_from,
        **kante.metadaten,
    )


def graph_speichern(G: nx.DiGraph, pfad: str) -> None:
    """
    Speichert den Graphen als Pickle-Datei.

    Args:
        G:    Der zu speichernde Graph.
        pfad: Dateipfad für die Ausgabedatei (z. B. "propra/data/graph.pkl").
    """
    ziel = Path(pfad)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "wb") as f:
        pickle.dump(G, f)
    print(f"Graph gespeichert: {ziel} ({G.number_of_nodes()} Knoten, {G.number_of_edges()} Kanten)")


def graph_laden(pfad: str) -> nx.DiGraph:
    """
    Lädt einen gespeicherten Graphen aus einer Pickle-Datei.

    Args:
        pfad: Dateipfad der gespeicherten Graphdatei.

    Returns:
        nx.DiGraph: Der geladene Graph.

    Raises:
        FileNotFoundError: Wenn die Datei nicht gefunden wird.
    """
    quelle = Path(pfad)
    if not quelle.exists():
        raise FileNotFoundError(
            f"Graphdatei nicht gefunden: {quelle}. "
            "Bitte zuerst einen Build-Script ausführen."
        )
    with open(quelle, "rb") as f:
        G = pickle.load(f)
    print(f"Graph geladen: {quelle} ({G.number_of_nodes()} Knoten, {G.number_of_edges()} Kanten)")
    return G


def graph_zusammenfassung(G: nx.DiGraph) -> dict:
    """
    Gibt eine Zusammenfassung des Graphen zurück — nützlich für Tests und Debugging.

    Returns:
        dict mit Anzahl Knoten, Kanten und Knotentypen.
    """
    knotentypen: dict[str, int] = {}
    for _, daten in G.nodes(data=True):
        typ = daten.get("type", "unbekannt")
        knotentypen[typ] = knotentypen.get(typ, 0) + 1

    kantentypen: dict[str, int] = {}
    for _, _, daten in G.edges(data=True):
        relation = daten.get("relation", "unbekannt")
        kantentypen[relation] = kantentypen.get(relation, 0) + 1

    return {
        "knoten_gesamt": G.number_of_nodes(),
        "kanten_gesamt": G.number_of_edges(),
        "knotentypen": knotentypen,
        "kantentypen": kantentypen,
        "quelle": G.graph.get("quelle", "unbekannt"),
        "jurisdiction": G.graph.get("jurisdiction", "unbekannt"),
    }

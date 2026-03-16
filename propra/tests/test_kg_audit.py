"""Structural tests for the Propra knowledge graph.

Runs the four audit checks (coverage, orphans, reference integrity, node types)
as pytest assertions so graph regressions are caught automatically on every test run.
"""

import pytest
from pathlib import Path

from propra.eval.kg_audit import (
    check_coverage,
    check_orphans,
    check_references,
    check_node_types,
)
from propra.graph.builder import load_graph

_GRAPH_PATH = Path(__file__).parent.parent / "data" / "graph.pkl"


@pytest.fixture(scope="module")
def G():
    if not _GRAPH_PATH.exists():
        pytest.skip("graph.pkl not found — run build_graph first")
    return load_graph(str(_GRAPH_PATH))


def test_kg_section_anchor_coverage(G):
    """Every registered law must have at least the expected number of section anchors."""
    lines = check_coverage(G)
    failures = [ln for ln in lines if ln.strip().startswith("[FAIL]")]
    assert not failures, "\n".join(failures)


def test_kg_no_orphan_nodes(G):
    """No law node should have zero edges (orphans indicate a build error)."""
    lines = check_orphans(G)
    failures = [ln for ln in lines if ln.strip().startswith("[FAIL]")]
    assert not failures, "\n".join(failures)


def test_kg_reference_edge_integrity(G):
    """Every 'references' edge must point to a node that exists in the graph."""
    lines = check_references(G)
    failures = [ln for ln in lines if ln.strip().startswith("[FAIL]")]
    assert not failures, "\n".join(failures)


def test_kg_node_types_valid(G):
    """All node types must be in the schema's NODE_TYPES set."""
    lines = check_node_types(G)
    failures = [ln for ln in lines if ln.strip().startswith("[FAIL]")]
    assert not failures, "\n".join(failures)

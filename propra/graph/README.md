# Knowledge graph

The core graph is **MBO only**, built section by section. One build, one output: `propra/data/graph.pkl`.

## Prerequisites

- Python 3.11+
- Dependencies from repo root: `pip install -r requirements.txt`

No API keys required.

---

## 1. Build the graph

Loads MBO nodes for the sections defined in `build_graph.py` (§1 for now), adds structural edges, section-defined edges (e.g. §1 exclusions), and reference edges. Writes `propra/data/graph.pkl` and `graph.graphml`.

```bash
python -m propra.graph.build_graph
```

To add more sections, edit `_SECTIONS` in `build_graph.py` and add the corresponding edges in `mbo_section_edges.py`.

---

## 2. Explore nodes (CLI)

```bash
python -m propra.graph.explore
# or: python -m propra.graph.explore propra/data/graph.pkl
```

Type a node ID (e.g. `MBO_§1_2.1`) or a substring. Empty input lists all node IDs.

---

## 3. Visualize (HTML)

```bash
python -m propra.graph.visualize_html
# optional: python -m propra.graph.visualize_html --filter §1
```

Output: `propra/data/graph.html`. Open in a browser.

---

## 4. Audit relations

```bash
python -m propra.graph.audit_relations
python -m propra.graph.audit_relations --relation sub_item_of --sample 20
python -m propra.graph.audit_relations --export propra/data/audit_edges.csv
```

---

## 5. Core nodes

```bash
python -m propra.graph.core_nodes
```

---

## File overview

| File | Role |
|------|------|
| `schema.py` | Node/edge types and validation |
| `builder.py` | Graph I/O: create_graph, add_node, add_edge, load_graph, save_graph |
| `build_graph.py` | Build core graph (MBO, sections in _SECTIONS) |
| `mbo_section_edges.py` | Section-defined edges (e.g. §1 exclusions 2.2–2.12 → 2.1) |
| `references_edges.py` | References parsed from node text |
| `parse_inventory.py` | Parse MBO_node_inventory.md → Node list |
| `explore.py` | Interactive CLI explorer |
| `visualize.py` | Export to GraphML |
| `visualize_html.py` | Export to HTML (pyvis) |
| `audit_relations.py` | Sample/export edges for review |
| `core_nodes.py` | List high-degree nodes |

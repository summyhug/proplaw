# Knowledge graph

The Propra knowledge graph is built from **node inventories** (Markdown) and **domain edge** modules. Colleagues can build, inspect, and audit it locally without extra services.

## Prerequisites

- Python 3.11+
- Dependencies from repo root: `pip install -r requirements.txt`

No API keys are required for build, explore, visualize, or audit (only for `edge_proposer`, which uses Claude).

---

## 1. Build the graph

Loads MBO + BW node inventories, adds structural edges (section anchors), fence domain edges, and reference edges parsed from node text. Writes `propra/data/graph.pkl` and `graph.graphml`.

```bash
# From repo root
python -m propra.graph.build_graph
```

You should see a summary of node counts, edge counts, and relation types. The first run creates the graph; later runs overwrite it.

---

## 2. Explore nodes (CLI)

Inspect a node and its neighbours by ID or search term:

```bash
python -m propra.graph.explore
# or with explicit graph path:
python -m propra.graph.explore propra/data/graph.pkl
```

At the prompt, type a node ID (e.g. `BW_LBO_§5_5.1`) or a substring. Enter with no input to list all node IDs.

---

## 3. Visualize (HTML)

Export the graph (or a filtered subgraph) to an interactive HTML file:

```bash
# Full graph (can be heavy)
python -m propra.graph.visualize_html

# Focused subgraph (e.g. fence-related §§)
python -m propra.graph.visualize_html --filter §5 §6 A1-07 §74
```

Output is written next to `graph.pkl`, e.g. `propra/data/graph.html` or `propra/data/graph_§5_§6_A1-07_§74.html`. Open in a browser. Structural edges are shown grey/dashed; domain and reference edges are bold.

---

## 4. Core nodes report

List the most connected nodes (by total degree or by semantic connections only):

```bash
python -m propra.graph.core_nodes
```

Useful to see which sections act as hubs (e.g. §66, §85a, §5).

---

## 5. Audit relations

Check that edges make sense by sampling or exporting them:

```bash
# Summary (counts per relation type, structural excluded)
python -m propra.graph.audit_relations

# Sample 15 edges per relation type for terminal review
python -m propra.graph.audit_relations --sample 15

# Focus on one relation type
python -m propra.graph.audit_relations --relation references --sample 30

# Export all non-structural edges to CSV for spreadsheet review
python -m propra.graph.audit_relations --export propra/data/audit_edges.csv
```

For a step-by-step audit workflow (what to check per relation type, suggested order), see [README_AUDIT.md](./README_AUDIT.md).

---

## Data pipeline (optional)

If you need to regenerate node inventories or clean source text:

| Step | Script | Purpose |
|------|--------|--------|
| Extract text from PDF | `python propra/data/extract_pdf.py propra/data/raw/MBO.pdf` | PDF → `.txt` (then clean if needed) |
| Clean MBO.txt after PDF import | `python propra/data/clean_mbo_txt.py` | Fix broken words, page numbers, blank lines |
| MBO.txt → node inventory | `python propra/data/txt_to_node_inventory.py` | Build `MBO_node_inventory.md` from `raw/MBO.txt` |

The graph build uses `MBO_node_inventory.md` and `BW_LBO_node_inventory.md`; you only need these scripts when updating source PDFs or the MBO text.

---

## File overview

| File | Role |
|------|------|
| `schema.py` | Node/edge types and validation |
| `builder.py` | `create_graph`, `add_node`, `add_edge`, `load_graph`, `save_graph` |
| `parse_inventory.py` | Parse Markdown inventories → `Node` list |
| `build_graph.py` | Main build: load nodes, structural edges, fence edges, reference edges |
| `fence_edges.py` | Domain edges for fence/Abstandsfläche (BW §5, §6, §50, §74, etc.) |
| `references_edges.py` | Extract § refs from node text → `references` edges |
| `explore.py` | Interactive CLI explorer |
| `visualize_html.py` | Export to HTML (pyvis) |
| `audit_relations.py` | Sample/export edges for review |
| `core_nodes.py` | Report high-degree nodes |
| `edge_proposer.py` | LLM-assisted edge proposals (requires `ANTHROPIC_API_KEY`) |

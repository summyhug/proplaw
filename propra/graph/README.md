# Knowledge graph

The graph contains **MBO** (section anchors; model structure) and **state LBOs** (e.g. **BbgBO**): full content nodes at sentence/list-item level, structural edges, and edges copied from MBO via section mapping. One build, one output: `propra/data/graph.pkl`. The product **cites only the LBO**; MBO is internal only. See `docs/GRAPH_ARCHITECTURE.md` and **`docs/ADDING_A_NEW_STATE.md`** to add another state.

## Prerequisites

- Python 3.11+
- Dependencies from repo root: `pip install -r requirements.txt`

No API keys required.

---

## 1. Build the graph

Loads MBO section anchors and each state in `_STATE_REGISTRY` from `data/node inventory/*_node_inventory_fine.md`, adds structural edges (supplements, sub_item_of), MBO section edges, state edges copied from MBO mapping, and reference edges. If a curated state module such as `bbgbo_section_edges.py` or `baybo_section_edges.py` exists, the build uses that file instead of the generic structural + mapping pass. Writes `propra/data/graph.pkl` and `graph.graphml`.

```bash
python -m propra.graph.build_graph
```

To **add a new state**, follow `docs/ADDING_A_NEW_STATE.md` (inventory → refine → mapping → register). To add more MBO sections, edit `_SECTIONS` in `build_graph.py` and edges in `mbo_section_edges.py`.

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
| `build_graph.py` | Build graph (MBO anchors + state LBOs in _STATE_REGISTRY) |
| `mbo_section_edges.py` | MBO section-defined edges (e.g. §1 exclusions, §6 exception_of) |
| `state_structural_edges.py` | sub_item_of for state content nodes (general; BbgBO uses `bbgbo_section_edges.py`) |
| `state_mbo_edges.py` | Copy MBO edges onto any state using data/{STATE}_mbo_mapping.json |
| `bbgbo_mbo_edges.py` | Backward-compatible Brandenburg wrapper around `state_mbo_edges.py` |
| `generate_state_section_edges.py` | Generate a reviewable `{state}_section_edges.py` draft from fine inventory + mapping |
| `generate_bbgbo_section_edges.py` | Regenerate `bbgbo_section_edges.py` draft (structural + MBO-projected) |
| `bbgbo_section_edges.py` | Single-file BbgBO section edges (supplements + sub_item_of + MBO-projected domain edges) |
| `references_edges.py` | References parsed from node text |
| `parse_inventory.py` | Parse data/node inventory/*_node_inventory.md → Node list |
| `map_to_mbo.py` | Generate state↔MBO section mapping (→ data/{STATE}_mbo_mapping.json) |
| `explore.py` | Interactive CLI explorer |
| `visualize.py` | Export to GraphML |
| `visualize_html.py` | Export to HTML (pyvis) |
| `audit_relations.py` | Sample/export edges for review |
| `core_nodes.py` | List high-degree nodes |

State inventories are refined to sentence level by `propra/data/split_inventory_to_sentences.py` before the build.

"""
Knowledge graph package for Propra.

Core graph: MBO only, built section by section (graph.pkl).

- schema.py, builder.py   — Node/edge types and graph I/O
- build_graph.py          — Build core graph (MBO §1, …)
- mbo_section_edges.py    — Section-defined edges (e.g. §1 exclusions)
- references_edges.py     — References parsed from node text
- parse_inventory.py      — Load node inventories (Markdown) into Node objects
- explore.py              — Interactive node explorer (CLI)
- visualize.py            — Export to GraphML
- visualize_html.py      — Export to interactive HTML (pyvis)
- audit_relations.py     — Sample/export edges for review
- core_nodes.py           — List high-connectivity nodes

See propra/graph/README.md for how to build and explore.
"""

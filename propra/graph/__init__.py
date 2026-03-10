"""
Knowledge graph package for Propra.

- schema.py, builder.py   — Node/edge types and graph I/O
- build_graph.py          — Build unified graph (MBO + BW, structural + domain edges)
- fence_edges.py          — Fence/Abstandsfläche domain edges (BW)
- references_edges.py    — References edges parsed from node text
- parse_inventory.py     — Load node inventories (Markdown) into Node objects
- explore.py              — Interactive node explorer (CLI)
- visualize_html.py      — Export graph to interactive HTML (pyvis)
- audit_relations.py     — Sample/export edges for relation review
- core_nodes.py           — Report high-connectivity (core) nodes

See propra/graph/README.md for how to build, explore, and audit the graph.
"""

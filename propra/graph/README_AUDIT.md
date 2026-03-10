# Auditing graph relations

How to systematically check that edges in the knowledge graph make sense.

## 1. Get a summary

```bash
python -m propra.graph.audit_relations
```

Shows edge counts per relation type (structural supplements excluded by default). Use this to see what you’re dealing with.

## 2. Sample edges per relation type

```bash
python -m propra.graph.audit_relations --sample 15
```

Prints up to 15 random edges per relation type, with:

- source and target node IDs  
- `sourced_from` (legal basis)  
- Short text preview for both nodes  
- Optional reasoning from metadata  

**Suggested order:** Start with small relation types (e.g. `exception_of`, `has_condition`, `overridden_by`), then do larger ones (`references`, `supplements`) with a sample.

## 3. Focus on one relation type

```bash
python -m propra.graph.audit_relations --relation references --sample 30
python -m propra.graph.audit_relations --relation exception_of --sample 10
```

Review whether the direction and target are correct (e.g. “A references B” = A’s text cites B’s paragraph).

## 4. Export to CSV for spreadsheet review

```bash
python -m propra.graph.audit_relations --export propra/data/audit_edges.csv
```

Opens in Excel/Google Sheets. Columns: `relation`, `source_id`, `target_id`, `sourced_from`, `source_paragraph`, `target_paragraph`, `source_type`, `target_type`, `source_text_preview`, `target_text_preview`. Filter by `relation` and scan for obvious errors.

To export only one relation type:

```bash
python -m propra.graph.audit_relations --relation references --export propra/data/refs_audit.csv
```

## 5. Include structural edges (optional)

By default, structural “section → anchor” supplements are excluded so you can focus on semantic edges. To include them:

```bash
python -m propra.graph.audit_relations --sample 5 --include-structural
```

## 6. Inspect a single node (explore)

For a specific node, use the interactive explorer:

```bash
python -m propra.graph.explore
# at prompt: type node ID or part of it, e.g. BW_LBO_§5_5.1 or §6-02
```

Shows all incoming and outgoing edges with relation type and short text.

## Suggested workflow

1. Run `audit_relations` (no args) to see counts.  
2. Run `--relation exception_of --sample 10` and `--relation has_condition --sample 5` (few edges, quick check).  
3. Run `--relation references --sample 30` (or 50) and skim: does “FROM” text actually cite “TO” paragraph?  
4. Export `--export audit.csv` and spot-check a few rows per relation in a spreadsheet.  
5. Use `explore` for any node you’re unsure about (e.g. core nodes from `python -m propra.graph.core_nodes`).

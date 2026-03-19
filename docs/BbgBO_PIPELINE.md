# BbgBO pipeline: PDF → text → nodes → MBO match → edge KG

Run these steps from the **repo root** after replacing `propra/data/raw/BbgBO.pdf` with the correct file.

---

## 1. PDF → text

Extract the new PDF to plain text (output goes to `propra/data/txt/`):

```bash
python propra/data/extract_pdf_clean.py propra/data/raw/BbgBO.pdf --out-dir propra/data/txt
```

Or re-extract all LBOs (including BbgBO):

```bash
python propra/data/bulk_extract.py --force
```

**Output:** `propra/data/txt/BbgBO.txt`

---

## 2. Text → paragraph-level node inventory

Generate a draft node inventory (one row per Absatz). Uses an LLM for type classification.

- **Anthropic (default):** set `ANTHROPIC_API_KEY` in `.env`
- **Gemini:** add `--provider gemini` and set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env`  
  (requires `pip install google-generativeai`)

```bash
# With Anthropic (default)
python propra/data/draft_inventory.py \
  --txt propra/data/txt/BbgBO.txt \
  --bundesland Brandenburg \
  --lbo_code BbgBO \
  --jurisdiction DE-BB \
  --version_date "siehe Amtsblatt" \
  --source_url "https://bravors.brandenburg.de/gesetze/bbgbo" \
  --output "propra/data/node inventory/BbgBO_node_inventory_v2.md"

# With Gemini
python propra/data/draft_inventory.py \
  --txt propra/data/txt/BbgBO.txt \
  --bundesland Brandenburg \
  --lbo_code BbgBO \
  --jurisdiction DE-BB \
  --version_date "siehe Amtsblatt" \
  --source_url "https://bravors.brandenburg.de/gesetze/bbgbo" \
  --output "propra/data/node inventory/BbgBO_node_inventory_v2.md" \
  --provider gemini
```

**Output:** `propra/data/node inventory/BbgBO_node_inventory_v2.md`  
Review and fix § titles / types if needed.

---

## 3. Paragraph-level → sentence-level (fine) inventory

Split to MBO-style granularity (e.g. `1.1`, `1.2`, `2.1`):

```bash
python -m propra.data.split_inventory_to_sentences \
  --input "propra/data/node inventory/BbgBO_node_inventory_v2.md" \
  --output "propra/data/node inventory/BbgBO_node_inventory_fine.md"
```

**Output:** `propra/data/node inventory/BbgBO_node_inventory_fine.md`  
Spot-check §1, §6; fix over-splits (e.g. at “Abs.”, “Nr.”) if necessary.

---

## 3b. Optional fine inventory cleanup (advanced)

If you see PDF artifacts in the fine inventory (e.g. `Bearbeitungsstand` watermarks,
over/under-splitting around list markers), you can run the optional cleanup helpers.
These scripts are reusable and take `--input/--output`.

Use a temp output file so you can compare before/after:

```bash
tmp="propra/data/node inventory/BbgBO_node_inventory_fine.cleaned.md"

python "propra/data/node inventory/cleanup_bearbeitungsstand.py" \
  --input "propra/data/node inventory/BbgBO_node_inventory_fine.md" \
  --output "$tmp"

python "propra/data/node inventory/fix_dangling_markers.py" \
  --input "$tmp" \
  --output "$tmp.2"

python "propra/data/node inventory/merge_reference_splits.py" \
  --input "$tmp.2" \
  --output "$tmp.3"

python "propra/data/node inventory/split_list_markers.py" \
  --input "$tmp.3" \
  --output "$tmp.4"
```

Then replace `BbgBO_node_inventory_fine.md` with the last cleaned file if the result looks good.

---

## 4. Match state §§ to MBO

Generate the section mapping used for edge generation:

```bash
python -m propra.graph.map_to_mbo --state BbgBO
```

**Output:** `propra/data/BbgBO_mbo_mapping.json`  
Edit `mapping` and `review` if any § matches are wrong.

---

## 5. Generate BbgBO section edges (draft from MBO)

Populate `bbgbo_section_edges.py` with:
- structural edges (`supplements`, `sub_item_of`) derived from the fine BbgBO inventory, and
- the MBO-projected domain edges from the MBO mapping,

so you have a single file to review and adapt:

```bash
PYTHONPATH=. python -m propra.graph.generate_bbgbo_section_edges
```

**Output:** `propra/graph/bbgbo_section_edges.py` is overwritten with generated edges.  
Edit this file to correct relation types (e.g. `exception_of` vs `supplements`) and add/remove edges.

---

## 6. Build the graph

```bash
python -m propra.graph.build_graph
```

**Output:** `propra/data/graph.pkl`, `propra/data/graph.graphml`  
Optional: run the HTML visualizer if you use it.

---

## Summary

| Step | Command / output |
|------|-------------------|
| 1. PDF → text | `extract_pdf_clean.py` or `bulk_extract.py --force` → `data/txt/BbgBO.txt` |
| 2. Text → nodes (paragraph) | `draft_inventory.py` → `data/node inventory/BbgBO_node_inventory_v2.md` |
| 3. Nodes → fine nodes | `split_inventory_to_sentences.py` → `BbgBO_node_inventory_fine.md` |
| 4. Match to MBO | `map_to_mbo --state BbgBO` → `data/BbgBO_mbo_mapping.json` |
| 5. Edges draft | `generate_bbgbo_section_edges` → `graph/bbgbo_section_edges.py` |
| 6. Build KG | `build_graph` → `data/graph.pkl` + `graph.graphml` |

# Node Inventory Guide

## What is a node inventory?

Before the knowledge graph (KG) can be built, every provision of every LBO must be catalogued. That catalogue is the node inventory — one `.md` file per LBO, listing every § or Art. with its classification.

Each row in the inventory becomes a `Node` object (see `propra/graph/schema.py`):

```python
Node(
    id="DE_BY_BayBO_Art6_01",
    type="abstandsflaeche",
    jurisdiction="DE-BY",
    source_paragraph="Art. 6 BayBO",
    text="Vor den Außenwänden...",
    numeric_value=0.4,
    unit="ratio",
)
```

The node **type** is the most critical field. Wrong type = wrong graph structure = wrong answers to users.

---

## Why .md format?

- Human-readable — open in VS Code and read like a document
- Structured enough for `propra/graph/parse_inventory.py` to extract nodes programmatically
- Easy to diff in git — every change is traceable
- Reviewable by non-developers without touching code

---

## How inventories are produced

```
PDF → extract_pdf_clean.py → data/txt/*.txt → draft_inventory.py → data/node inventory/*_node_inventory.md
```

The draft is generated using the Anthropic API to classify each provision. It is always a **draft** — manual review and correction is required before committing.

Run bulk extraction and drafting:
```bash
python propra/data/bulk_extract.py
python propra/data/bulk_inventory.py
```

---

## The 83 node types — quick reference

Node types fall into logical groups matching the structure of every LBO:

| Group | Types | Typical §§ |
|---|---|---|
| Scope & definitions | `anwendungsbereich`, `begriffsbestimmung`, `allgemeine_anforderung` | 1–3 |
| Land & building | `grundstuecksbebauung`, `abstandsflaeche`, `abstandsflaeche_sonderfall`, `abstandsflaechenübertragung`, `gelaendehoehe` | 4–10 |
| Construction elements | `tragende_wand`, `brandwand`, `aussenwand`, `trennwand`, `decke`, `dach`, `treppe`, `treppenraum`, `fensteroffnung` | 25–45 |
| Fire & safety | `brandschutzanforderung`, `standsicherheit`, `schutzanforderung`, `verkehrssicherheit` | 14–30 |
| Permits & procedures | `genehmigungspflicht`, `verfahrensfreiheit`, `vereinfachtes_genehmigungsverfahren`, `bauantrag`, `baugenehmigung`, `verfahrensfrist` | 50–75 |
| Special | `zahlenwert`, `schlussvorschrift`, `ermaechtigungsgrundlage`, `sonderbautyp`, `barrierefreiheit` | last §§ |

Full list of all 83 types: `propra/graph/schema.py` → `NODE_TYPES`.

**Note on `zahlenwert`:** only use for standalone numeric threshold nodes (e.g. "3 m Mindestabstand"). A full § that contains numbers is still its primary type (e.g. `abstandsflaeche`), not `zahlenwert`.

**Note on `allgemeine_anforderung`:** this is the API's fallback when uncertain. Too many of these in the permit section (§§ 50+) means the API got confused — correct those manually.

---

## Expected structure per LBO

Use this as your mental map when reviewing:

| §§ range | Expected types |
|---|---|
| § 1 | `anwendungsbereich` |
| § 2 | `begriffsbestimmung` |
| § 3 | `allgemeine_anforderung` |
| §§ 4–5 | `grundstuecksbebauung`, `abstandsflaeche` |
| §§ 6–15 | `abstandsflaeche_sonderfall`, `gestaltungsanforderung`, `brandschutzanforderung` |
| §§ 16–45 | construction element types |
| §§ 50+ | `genehmigungspflicht`, `bauantrag`, `baugenehmigung`, `verfahrensfrist` |
| Last 3–5 §§ | `schlussvorschrift`, `ermaechtigungsgrundlage` |

BayBO uses `Art.` instead of `§` — structure is identical.

---

## Quality checklist — review every inventory before committing

**1. Does it start at § 1 / Art. 1?**
If it starts mid-document (e.g. § 16a), the TOC stripping failed. Do not commit — fix the extractor and re-extract.

**2. Are § numbers sequential without gaps?**
Gaps may mean provisions were dropped. Missing §§ should be added manually.

**3. Are types sensible for each § number?**
Cross-check against the expected structure table above.

**4. Are there duplicate § numbers?**
Two entries for `§ 2` means the PDF had a comparison table. Flag for extractor fix.

**5. Are titles bleeding into body text?**
`§ 4 | Bebauung der Grundstücke Gebäude dürfen nur...` — title and body on one line. Flag for extractor fix.

**6. Is the permit section classified correctly?**
The §§ 50+ are the most error-prone. `genehmigungspflicht`, `bauantrag`, `baugenehmigung` should dominate — not `allgemeine_anforderung`.

---

## What to fix where

| Issue | Fix in |
|---|---|
| § 1 not first provision | `extract_pdf_clean.py` via Claude Code |
| Duplicate provisions | `extract_pdf_clean.py` via Claude Code |
| Title bleeding into body | `extract_pdf_clean.py` via Claude Code |
| Structural headers as provisions | `extract_pdf_clean.py` via Claude Code |
| Wrong node type classification | Edit `.md` file directly |
| Missing title (known PDF limitation) | Edit `.md` file directly |
| Truncated body text | Edit `.md` file directly |

---

## Review workflow per LBO

1. Open `propra/data/node inventory/{LBO}_node_inventory.md` in VS Code
2. Confirm file starts at § 1 / Art. 1
3. Scan § numbers top to bottom — sequence must be complete
4. Check types in the permit section (§§ 50+) — most common errors here
5. Correct wrong types directly in the `.md`
6. Commit: `[lbo-XX-name] Review and correct node inventory`

Expect 10–15% of API classifications to need manual correction. This is normal.

---

## Known limitations

| LBO | Known issue |
|---|---|
| BauO_NRW | § 1 has no title — NRW PDF footnotes overlap the heading in raw extraction |
| BayBO | Uses `Art.` not `§` — handled by parser, no action needed |
| MBO | Two-column TOC layout — verify § 1 is starting point after extraction |

---

## File naming convention

| File | Description |
|---|---|
| `propra/data/raw/{LBO}.pdf` | Original source PDF |
| `propra/data/txt/{LBO}.txt` | Cleaned extracted text (from extract_pdf_clean.py) |
| `propra/data/node inventory/{LBO}_node_inventory.md` | Draft node inventory (review before use) |

Jurisdiction codes: `DE-BW`, `DE-BY`, `DE-BE`, `DE-BB`, `DE-HB`, `DE-HH`, `DE-HE`, `DE-MV`, `DE-NI`, `DE-NW`, `DE-RP`, `DE-SL`, `DE-SN`, `DE-ST`, `DE-SH`, `DE-TH`

---

## Adding a state to the graph

After you have a reviewed paragraph-level inventory, the graph needs a **sentence-level** version and (optionally) a **section mapping** to MBO. See **`docs/ADDING_A_NEW_STATE.md`** for the full steps (refine granularity → mapping → register in build). You can do this with Cursor or Claude by following that guide.